#pragma once
#include "s760_native_runtime.hpp"
#include "s760_native_stream.hpp"
#include "s760_native_rate_converter.hpp"
#include <cstring>
#include "s760_media_library.hpp"

namespace s760 {
// Explicit little-endian encoding; never serialize C++ structs/pointers/padding.
// All allocation and validation take place off the realtime callback.
struct NativePluginState {
    static constexpr std::size_t max_bytes=266u*1024*1024;
    unsigned version=3,rate=44100,max_block=512;
    MediaLibrary::Snapshot media;
    bool has_stream=false;
    std::uint64_t origin=0;
    std::vector<std::uint8_t> identity,machine;
    NativeStream::Snapshot stream;
    NativeRateConverter::Snapshot converter;

    struct Writer {
        std::vector<std::uint8_t> bytes;
        void integer(std::uint64_t value,unsigned count=4) {for(unsigned i=0;i<count;++i) bytes.push_back(std::uint8_t(value>>(i*8)));}
        void text(const std::string& value) {blob({value.begin(),value.end()});}
        void pcm(float value) {std::uint32_t bits;std::memcpy(&bits,&value,4);integer(bits);}
        void blob(const std::vector<std::uint8_t>& value) {integer(value.size());bytes.insert(bytes.end(),value.begin(),value.end());}
    };
    struct Reader {
        const std::vector<std::uint8_t>& bytes;std::size_t offset=0;
        std::uint64_t integer(unsigned count=4) {
            if(count>bytes.size()-offset) throw std::invalid_argument("Truncated plugin state");
            std::uint64_t value=0;for(unsigned i=0;i<count;++i) value|=std::uint64_t(bytes[offset++])<<(i*8);return value;
        }
        std::string text() {auto b=blob(MediaLibrary::max_path);return {b.begin(),b.end()};}
        float pcm() {std::uint32_t bits=std::uint32_t(integer());float value;std::memcpy(&value,&bits,4);
            if(!std::isfinite(value)) throw std::invalid_argument("Nonfinite plugin state PCM");return value;}
        std::vector<std::uint8_t> blob(std::size_t limit) {
            auto size=integer();if(size>limit || size>bytes.size()-offset) throw std::invalid_argument("Oversized plugin state section");
            auto begin=bytes.begin()+offset;offset+=size;return {begin,begin+size};
        }
    };
    void validate() const {
        if(!NativeRateConverter::supported(rate) || !max_block || max_block>1024 || identity.size()!=160 ||
           machine.empty() || machine.size()>257u*1024*1024 || origin>9007199254740991ULL)
            throw std::invalid_argument("Invalid plugin state profile");
        if(version!=1 && version!=2 && version!=3) throw std::invalid_argument("Invalid state version");
        if(version>=2) media.validate();
        if(!has_stream) return;
        if(version<3) for(const auto& block:stream.pending) for(unsigned i=0;i<block.frames*2;++i)
            if(block.input[i]!=0.f)throw std::invalid_argument("Legacy state cannot preserve input PCM");
        if(converter.rate!=rate || converter.host_cursor!=stream.completed ||
           stream.delay_frames!=NativeRateConverter::host_samples(NativeStream::output_delay,rate) ||
           stream.batch_frames!=NativeRateConverter::host_samples(2048,rate))
            throw std::invalid_argument("Plugin/converter/queue clock mismatch");
        NativeRateConverter check_converter(converter,[](float*,std::size_t){return false;});
        NativeStream check_stream([](const NativeStream::Block&,float*){return false;},stream);
    }
    std::vector<std::uint8_t> encode() const {
        validate();Writer w;w.integer(version);w.integer(rate);w.integer(max_block);w.integer(has_stream);w.integer(origin,8);w.blob(identity);w.blob(machine);
        if(has_stream) {
            w.integer(converter.version);w.integer(converter.rate);w.integer(converter.host_cursor,8);w.integer(converter.native_cursor,8);
            for(auto value:converter.history) w.pcm(value);
            w.integer(stream.version);w.integer(stream.delay_frames);w.integer(stream.batch_frames);w.integer(stream.clock,8);w.integer(stream.completed,8);
            w.integer(stream.pending.size());
            for(const auto& b:stream.pending) {
                w.integer(b.first,8);w.integer(b.frames);w.integer(b.events);
                for(unsigned i=0;i<b.events;++i) {w.integer(b.midi[i].offset);for(auto byte:b.midi[i].bytes) w.integer(byte,1);}
                if(version>=3)for(unsigned i=0;i<b.frames*2;++i)w.pcm(b.input[i]);
            }
            w.integer(stream.pcm.size());for(auto value:stream.pcm) w.pcm(value);
        }
        if(version>=2) {w.text(media.folder);w.text(media.selected);w.text(media.inserted);w.integer(media.paths.size());for(const auto& path:media.paths) w.text(path);}
        auto sum=native_digest(w.bytes);
        std::vector<std::uint8_t> out{'S','7','6','0','N','P','S','1'};
        out.insert(out.end(),sum.begin(),sum.end());out.insert(out.end(),w.bytes.begin(),w.bytes.end());return out;
    }
    static NativePluginState decode(const std::vector<std::uint8_t>& archive) {
        if(archive.size()<40 || archive.size()>max_bytes || std::memcmp(archive.data(),"S760NPS1",8)) throw std::invalid_argument("Invalid plugin state header");
        std::vector<std::uint8_t> payload(archive.begin()+40,archive.end());auto sum=native_digest(payload);
        if(!std::equal(sum.begin(),sum.end(),archive.begin()+8)) throw std::invalid_argument("Plugin state checksum mismatch");
        Reader r{payload};NativePluginState s;
        s.version=unsigned(r.integer());if(s.version!=1 && s.version!=2 && s.version!=3) throw std::invalid_argument("Unsupported plugin state version");
        s.rate=unsigned(r.integer());s.max_block=unsigned(r.integer());auto has=r.integer();
        if(has>1) throw std::invalid_argument("Invalid stream marker");s.has_stream=has!=0;s.origin=r.integer(8);s.identity=r.blob(160);s.machine=r.blob(257u*1024*1024);
        if(s.has_stream) {
            auto& c=s.converter;c.version=unsigned(r.integer());c.rate=unsigned(r.integer());c.host_cursor=r.integer(8);c.native_cursor=r.integer(8);
            for(auto& value:c.history) value=r.pcm();
            auto& q=s.stream;q.version=unsigned(r.integer());q.delay_frames=unsigned(r.integer());q.batch_frames=unsigned(r.integer());q.clock=r.integer(8);q.completed=r.integer(8);
            auto count=r.integer();if(count>NativeStream::queue_blocks) throw std::invalid_argument("Too many pending blocks");
            q.pending.resize(std::size_t(count));
            for(auto& b:q.pending) {
                b.first=r.integer(8);b.frames=unsigned(r.integer());b.events=unsigned(r.integer());
                if(b.frames>NativeStream::max_frames || b.events>NativeStream::max_events) throw std::invalid_argument("Too many pending events");
                for(unsigned i=0;i<b.events;++i) {b.midi[i].offset=unsigned(r.integer());for(auto& byte:b.midi[i].bytes) byte=std::uint8_t(r.integer(1));}
                if(s.version>=3)for(unsigned i=0;i<b.frames*2;++i)b.input[i]=r.pcm();
            }
            count=r.integer();if(count>65536) throw std::invalid_argument("Too much queued PCM");q.pcm.resize(std::size_t(count));for(auto& value:q.pcm)value=r.pcm();
        }
        if(s.version>=2) {s.media.folder=r.text();s.media.selected=r.text();s.media.inserted=r.text();auto n=r.integer();if(n>MediaLibrary::max_entries) throw std::invalid_argument("Too many media entries");for(unsigned i=0;i<n;++i)s.media.paths.push_back(r.text());}
        if(r.offset!=payload.size()) throw std::invalid_argument("Trailing plugin state data");s.validate();return s;
    }
};
}
