// license:BSD-3-Clause
// Read-only experimental D1 fixture, not a complete BlueSCSI target.
#ifndef MAME_ROLAND_S760_TOOLBOX_FIXTURE_H
#define MAME_ROLAND_S760_TOOLBOX_FIXTURE_H
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <string>
#include <vector>
#include <algorithm>
#include <filesystem>

class s760_toolbox_fixture
{
public:
 struct reply { std::vector<uint8_t> data; uint8_t asc = 0; size_t data_out = 0; };
 void configure(const char *root, const char *target) {
  m_root = root ? root : "";
  m_target = !m_root.empty() && target && target[0] >= '0' && target[0] <= '6' && !target[1] ? target[0]-'0' : -1;
  invalidate();
  m_directory = "/Files";
 }
 bool enabled(int target) const { return m_target >= 0 && target == m_target; }
 static bool command(uint8_t opcode) { return opcode == 0xd0 || opcode == 0xd1 || opcode == 0xd2 || opcode == 0xd9; }
 void invalidate() { m_open = false; m_file.clear(); }
 void reset() { invalidate();m_directory = "/Files"; }
 reply set_directory(const std::vector<uint8_t> &data) {
  std::string path(data.begin(), std::find(data.begin(),data.end(),0));
  if (path.empty()) path = "/Files";
  std::filesystem::path resolved;
  if (!directory_path(path,resolved)) return fail(0x24);
  m_directory = path;
  return {};
 }
 reply execute(const uint8_t *cdb) {
  if (cdb[0] == 0xd1) return read(cdb);
  if (cdb[0] == 0xd9) {
   for (int i=2;i<8;++i) if (cdb[i]) return fail(0x24);
   if (cdb[9]) return fail(0x24);
   const size_t length=cdb[8];reply out;
   if (cdb[1]==2) { out.data_out=std::min<size_t>(64,length);return out; }
   if (cdb[1]==3) {
    out.data.assign(length ? length : 256,0);
    std::copy_n(m_directory.begin(),std::min(m_directory.size(),out.data.size()),out.data.begin());
    return out;
   }
   if (length>8 || cdb[1]>1) return fail(0x24);
   out.data.assign(8,cdb[1] ? 0 : 255);
   if (cdb[1]==0) out.data[m_target]=0; // fixture group contains only its fixed-disk target
   else out.data[1]=4; // SET_WORKING_DIR only, no multi-block or send capability
   out.data.resize(length ? length : 8);return out;
  }
  if (cdb[0]!=0xd0 && cdb[0]!=0xd2) return fail(0x20);
  for (int i=1;i<10;++i) if (cdb[i]) return fail(0x24);
  std::vector<entry> entries;if (!listing(entries)) return fail(0x24);
  reply out;
  if (cdb[0]==0xd2) { out.data.push_back(uint8_t(entries.size()));return out; }
  out.data.assign(entries.size()*40,0);
  for (size_t i=0;i<entries.size();++i) {
   const auto &e=entries[i];auto *row=out.data.data()+40*i;row[0]=uint8_t(i);row[1]=e.directory ? 0 : 1;
   std::copy_n(e.name.begin(),std::min<size_t>(32,e.name.size()),row+2);
   for (int n=0;n<5;++n) row[35+n]=uint8_t(e.size>>(32-8*n));
  }
  return out;
 }
 reply read(const uint8_t *cdb) {
  // This fixture supports one 4KiB block per command, no advertised capabilities.
  if (cdb[0] != 0xd1 || cdb[6] > 1 || cdb[7] || cdb[8] || cdb[9]) return fail(0x24);
  const uint32_t block = (uint32_t(cdb[2])<<24) | (uint32_t(cdb[3])<<16) | (uint32_t(cdb[4])<<8) | cdb[5];
  if (block > 0xfffff) return fail(0x21); // no uint32 byte-offset wrap
  if (!block) {
   invalidate();
   std::vector<entry> entries;
   if (!listing(entries) || cdb[1]>=entries.size() || entries[cdb[1]].directory) return fail(0x24);
   std::ifstream input(entries[cdb[1]].path, std::ios::binary | std::ios::ate);
   if (!input) return fail(0x24);
   const auto size = input.tellg();
   if (size < 0 || uint64_t(size) > 32*1024*1024) return fail(0x24);
   m_file.resize(size_t(size));input.seekg(0);
   if (size && !input.read(reinterpret_cast<char *>(m_file.data()), size)) return fail(0x24);
   m_open = true;
  }
  // Intentional deterministic error for a closed handle; physical behavior unqualified.
  if (!m_open) return fail(0x24);
  const uint64_t start = uint64_t(block)*4096;
  const size_t count = start < m_file.size() ? std::min<size_t>(4096,m_file.size()-size_t(start)) : 0;
  reply out;
  if (count) out.data.assign(m_file.begin()+size_t(start),m_file.begin()+size_t(start)+count);
  if (start+count >= m_file.size()) invalidate();
  return out;
 }
private:
 struct entry { std::filesystem::path path;std::string name;bool directory;uint64_t size; };
 bool directory_path(const std::string &path,std::filesystem::path &out) const {
  if (path!="/Files" && path.compare(0,7,"/Files/")!=0) return false;
  std::error_code ec;out=std::filesystem::path(m_root);
  if (!std::filesystem::is_directory(out,ec) || ec) return false;
  if (path=="/Files") return true;
  size_t start=7;
  while (start<path.size()) {
   auto end=path.find('/',start);auto part=path.substr(start,end==std::string::npos ? end : end-start);
   if (part.empty() || part=="." || part==".." || part.find_first_of("\\:")!=std::string::npos) return false;
   out/=part;
   if (std::filesystem::is_symlink(std::filesystem::symlink_status(out,ec)) || ec || !std::filesystem::is_directory(out,ec) || ec) return false;
   if (end==std::string::npos) break;
   start=end+1;
  }
  return true;
 }
 bool listing(std::vector<entry> &out) const {
  std::filesystem::path folder;if (!directory_path(m_directory,folder)) return false;
  std::error_code ec;
  std::filesystem::directory_iterator it(folder,ec),end;if (ec) return false;
  for (;it!=end;it.increment(ec)) {
   if (ec) return false;
   const auto &f=*it;auto name=f.path().filename().string();
   if (name.empty() || name[0]=='.' || f.is_symlink(ec)) continue;
   if (ec) return false;
   const bool dir=f.is_directory(ec);if (ec) return false;
   if (!dir && !f.is_regular_file(ec)) continue;
   if (ec) return false;
   const uint64_t size=dir ? 0 : f.file_size(ec);if (ec || size>0xffffffffffULL) return false;
   out.push_back({f.path(),name,dir,size});if (out.size()>100) return false;
  }
  if (ec) return false;
  std::sort(out.begin(),out.end(),[](const entry &a,const entry &b){return a.name<b.name;});
  return true;
 }
 reply fail(uint8_t asc) { invalidate();reply out;out.asc=asc;return out; }
 std::string m_root;
 std::string m_directory = "/Files";
 int m_target = -1;
 bool m_open = false;
 std::vector<uint8_t> m_file;
};
#endif
