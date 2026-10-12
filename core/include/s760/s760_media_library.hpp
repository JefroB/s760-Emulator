#pragma once
#include <algorithm>
#include <cctype>
#include <filesystem>
#include <stdexcept>
#include <string>
#include <mutex>
#include <vector>

namespace s760 {
// Host-owned browser metadata. Mounted bytes remain in the native checkpoint.
// No file I/O on the audio callback; configure is an explicit control action.
class MediaLibrary {
public:
    static constexpr std::size_t max_entries=1024, max_path=4096;
    struct Snapshot {
        std::string folder, selected, inserted;
        std::vector<std::string> paths;
        void validate() const {
            auto valid=[](const std::string& p) {
                return p.size()<=max_path && std::none_of(p.begin(),p.end(),[](unsigned char c){return c<32;});
            };
            if(paths.size()>max_entries || !valid(folder) || !valid(selected) || !valid(inserted))
                throw std::invalid_argument("Invalid media metadata");
            for(const auto& p:paths) if(p.empty() || !valid(p)) throw std::invalid_argument("Invalid media path");
            if(!selected.empty() && std::find(paths.begin(),paths.end(),selected)==paths.end())
                throw std::invalid_argument("Selected media is outside the inventory");
        }
    };
    Snapshot state() const {std::lock_guard<std::mutex> lock(mutex_);return state_;}
    std::string error() const {std::lock_guard<std::mutex> lock(mutex_);return error_;}
    void restore(const Snapshot& s) {s.validate();auto copy=s;commit(std::move(copy));}
    bool configure(const std::string& folder) {
        try {
            if(folder.empty()) throw std::invalid_argument("Choose a media folder");
            auto root=std::filesystem::absolute(std::filesystem::u8path(folder)).lexically_normal();
            if(!std::filesystem::is_directory(root)) throw std::invalid_argument("Media folder does not exist: "+folder);
            Snapshot next=state();next.folder=root.u8string();next.paths.clear();
            std::size_t inspected=0;
            for(auto it=std::filesystem::recursive_directory_iterator(root);it!=std::filesystem::recursive_directory_iterator();++it) {
                if(++inspected>100000 || it.depth()>32) throw std::runtime_error("Media scan exceeds directory limit; choose a smaller folder");
                if(it->is_symlink()) {it.disable_recursion_pending();continue;}
                auto ext=it->path().extension().u8string();
                std::transform(ext.begin(),ext.end(),ext.begin(),[](unsigned char c){return char(std::tolower(c));});
                if(ext==".img" && it->is_regular_file()) {
                    if(next.paths.size()==max_entries) throw std::runtime_error("Media library exceeds 1024 images; choose a smaller folder");
                    next.paths.push_back(it->path().u8string());
                }
            }
            std::sort(next.paths.begin(),next.paths.end());
            if(std::find(next.paths.begin(),next.paths.end(),next.selected)==next.paths.end())
                next.selected=next.paths.empty()?"":next.paths.front();
            next.validate();commit(std::move(next));return true;
        } catch(const std::exception& e) {std::lock_guard<std::mutex> lock(mutex_);error_=e.what();return false;}
    }
    bool select(const std::string& path) {
        std::lock_guard<std::mutex> lock(mutex_);
        if(std::find(state_.paths.begin(),state_.paths.end(),path)==state_.paths.end()) {
            error_="Image is not in this library";return false;
        }
        state_.selected=path;error_.clear();return true;
    }
    // Prepare before insertion so allocation/validation cannot fail after media changes.
    Snapshot with_inserted(const std::string& path) const {
        Snapshot next=state();next.inserted=path;next.selected=path;
        if(std::find(next.paths.begin(),next.paths.end(),path)==next.paths.end()) {
            if(next.paths.size()==max_entries) throw std::runtime_error("Media library is full");
            next.paths.push_back(path);
        }
        next.validate();return next;
    }
    void inserted(const std::string& path) {restore(with_inserted(path));}
    void commit(Snapshot&& next) {std::lock_guard<std::mutex> lock(mutex_);state_=std::move(next);error_.clear();}
private:
    mutable std::mutex mutex_;
    Snapshot state_;
    std::string error_;
};
}
