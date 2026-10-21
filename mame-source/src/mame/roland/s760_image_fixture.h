// license:BSD-3-Clause
// Opt-in, bounded image-switch qualification profile. Not a complete BlueSCSI.
#ifndef MAME_ROLAND_S760_IMAGE_FIXTURE_H
#define MAME_ROLAND_S760_IMAGE_FIXTURE_H
#include <algorithm>
#include <array>
#include <cctype>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <string>
#include <vector>

class s760_image_fixture
{
public:
 struct state { bool ejected=false, attention=false, failed=false, writable=false; uint8_t qualifier=0; std::string selected; };
 struct listing { std::vector<std::filesystem::path> paths; bool overflow=false; };
 void configure(const char *root,const char *stall_after=nullptr,const char *write_reset_after=nullptr) {
  m_root=root ? root : "";reset();m_stall_enabled=false;m_stall_used=false;m_stall_active=false;
  if (!m_root.empty() && stall_after && *stall_after) {
   char *end=nullptr;const auto value=std::strtoul(stall_after,&end,10);
   if (end && !*end && value<4000) { m_stall_after=size_t(value);m_stall_enabled=true; }
  }
  m_write_reset_after=0;m_write_reset_used=false;
  if (!m_root.empty() && write_reset_after && *write_reset_after) {
   const std::string text(write_reset_after);
   if (std::all_of(text.begin(),text.end(),[](unsigned char c){return c>='0' && c<='9';})) {
    char *end=nullptr;const auto value=std::strtoul(write_reset_after,&end,10);
    if (end && !*end && value>0 && value<=0xffffff) m_write_reset_after=size_t(value);
   }
  }
 }
 // Diagnostic host-timeline fault, never checkpointed or rearmed by guest reset.
 // Completed commands are deliberately excluded; backing persistence is separate.
 bool write_reset_pending() const { return m_write_reset_after && !m_write_reset_used; }
 bool interrupt_write(size_t transferred,size_t total) {
  if (!m_write_reset_used && m_write_reset_after && transferred>=m_write_reset_after && transferred<total) {
   m_write_reset_used=true;return true;
  }
  return false;
 }
 void reset() { m_state={}; }
 void invalidate() { release_stall();for (auto &s:m_state) { s={};s.failed=true; } }
 // Diagnostic PIO fault, disabled by default: one D7 holds BSY without REQ
 // after the configured byte count. Host-timeline state is not checkpointed.
 bool stall_listing(size_t transferred) {
  if (m_stall_enabled && !m_stall_used && transferred>=m_stall_after) {
   m_stall_used=true;m_stall_active=true;
  }
  return m_stall_active;
 }
 void release_stall() { m_stall_active=false; }
 bool enabled(int target) const {
  std::error_code ec;
  return !m_root.empty() && target>=0 && target<7 && std::filesystem::is_directory(directory(target),ec);
 }
 static bool command(uint8_t op) { return op==0xd7 || op==0xd8 || op==0xda || op==0xd9; }
 state &media(int target) { return m_state[target]; }
 listing list(int target) const {
  listing out; std::error_code ec;
  std::filesystem::directory_iterator it(directory(target),ec),end;
  for (; !ec && it!=end; it.increment(ec)) {
   if (it->is_symlink(ec) || !it->is_regular_file(ec)) continue;
   const auto name=it->path().filename().string();
   if (!valid(name)) continue;
   out.paths.push_back(it->path());
  }
  // Deterministic host-fixture ordering, not a FAT iteration-order claim.
  std::sort(out.paths.begin(),out.paths.end());out.overflow=out.paths.size()>100;
  return out;
 }
 std::vector<uint8_t> rows(const listing &entries) const {
  const size_t count=std::min<size_t>(100,entries.paths.size());std::vector<uint8_t> data(count*40,0);
  for (size_t i=0;i<count;++i) {
   auto *r=data.data()+i*40;r[0]=uint8_t(i);r[1]=1;
   const auto name=entries.paths[i].filename().string();std::copy_n(name.begin(),std::min<size_t>(32,name.size()),r+2);
   std::error_code ec;const uint64_t bytes=std::filesystem::file_size(entries.paths[i],ec);
   for (int n=0;n<5;++n) r[35+n]=uint8_t(bytes>>(32-8*n));
  }
  return data;
 }
 bool select(int target,size_t index,size_t block_size,std::vector<uint8_t> &image) {
  const auto entries=list(target);auto &s=media(target);
  // Upstream closes the old backing file before the new open and drops failure.
  image.clear();s.failed=true;s.attention=false;s.ejected=false;s.writable=false;s.selected.clear();
  if (index>=entries.paths.size()) return false;
  std::ifstream in(entries.paths[index],std::ios::binary|std::ios::ate);
  if (!in) return false;const auto size=in.tellg();
  // Fixture-only allocation ceiling: allow full CDs while bounding host memory.
  // This is not a BlueSCSI or native S-760 image-size limit.
  if (size<=0 || uint64_t(size)>uint64_t(1024)*1024*1024 || uint64_t(size)%block_size) return false;
  image.resize(size_t(size));in.seekg(0);in.read(reinterpret_cast<char*>(image.data()),size);
  if (!in) { image.clear();return false; }
  std::error_code ec;
  const auto permissions=std::filesystem::status(entries.paths[index],ec).permissions();
  const auto write_bits=std::filesystem::perms::owner_write|std::filesystem::perms::group_write|std::filesystem::perms::others_write;
  s.writable=block_size==512 && !ec && (permissions&write_bits)!=std::filesystem::perms::none;
  s.selected=entries.paths[index].filename().string();s.failed=false;s.ejected=true;return true;
 }
 // This opt-in fixture models completed device WRITE commands against its
 // selected backing file. Ordinary native media still use explicit export.
 bool write(int target,uint64_t offset,const std::vector<uint8_t> &data,size_t image_size) {
  auto &s=media(target);
  if (!s.writable || s.failed || s.ejected || s.selected.empty()) return false;
  const auto path=directory(target)/s.selected;std::error_code ec;
  const auto info=std::filesystem::symlink_status(path,ec);
  if (ec || !std::filesystem::is_regular_file(info)
      || std::filesystem::file_size(path,ec)!=image_size || ec
      || offset>image_size || data.size()>image_size-offset) { s.failed=true;return false; }
  std::fstream out(path,std::ios::binary|std::ios::in|std::ios::out);
  if (out) { out.seekp(std::streamoff(offset));out.write(reinterpret_cast<const char*>(data.data()),std::streamsize(data.size()));out.flush(); }
  if (!out) { s.failed=true;return false; }
  return true;
 }
 void close(int target) { auto &s=media(target);if (s.ejected) { s.ejected=false;s.attention=true; } }
 void eject(int target,size_t block_size,std::vector<uint8_t> &image) {
  auto &s=media(target);if (s.ejected) { close(target);return; }
  const auto entries=list(target);size_t index=0;
  for (size_t i=0;i<entries.paths.size();++i) if (entries.paths[i].filename().string()==s.selected) index=(i+1)%entries.paths.size();
  select(target,index,block_size,image);
 }
private:
 bool m_stall_enabled=false,m_stall_used=false,m_stall_active=false;
 size_t m_stall_after=0;
 size_t m_write_reset_after=0;bool m_write_reset_used=false;
 std::filesystem::path directory(int target) const { return std::filesystem::path(m_root)/("CD"+std::to_string(target)); }
 static bool valid(const std::string &name) {
  if (name.empty() || !std::isalnum(static_cast<unsigned char>(name[0]))) return false;
  std::string ext=std::filesystem::path(name).extension().string();
  std::transform(ext.begin(),ext.end(),ext.begin(),[](unsigned char c){return char(std::tolower(c));});
  static const char *ignored[]={".rom_loaded",".cue",".txt",".rtf",".md",".nfo",".pdf",".doc",".ini",".mid",".midi",".aiff",".mp3",".m4a",".ori",".tar",".tgz",".gz",".bz2",".tbz2",".xz",".zst",".z",".zip",".zipx",".rar",".lzh",".lha",".lzo",".lz4",".arj",".dmg",".hqx",".cpt",".7z",".s7z",".wav",".mar"};
  return std::none_of(std::begin(ignored),std::end(ignored),[&](const char *v){return ext==v;});
 }
 std::string m_root;
 std::array<state,7> m_state;
};
#endif
