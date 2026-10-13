#include "../src/s760_asio.cpp"
#include <cassert>
#include <thread>
#include <vector>
int main(){
    auto r=std::make_unique<Ring>();std::vector<float> pcm(capacity*2),out(capacity*2);
    for(unsigned i=0;i<pcm.size();++i)pcm[i]=float(i);
    assert(r->write(pcm.data(),capacity)==capacity);
    assert(r->write(pcm.data(),1)==0);
    assert(r->read(out.data(),capacity)==capacity);assert(pcm==out);
    assert(r->read(out.data(),1)==0);
    float invalid[4]={NAN,INFINITY,-2,2},finite[4];
    assert(r->write(invalid,2,true)==2);assert(r->read(finite,2)==2);
    assert(finite[0]==0 && finite[1]==0 && finite[2]==-1 && finite[3]==1);
    for(unsigned i=0;i<4;++i){assert(r->write(pcm.data(),capacity)==capacity);assert(r->read(out.data(),capacity)==capacity);assert(pcm==out);}
    std::thread producer([&]{for(unsigned i=0;i<100000;++i){float p[2]={float(i),-float(i)};while(!r->write(p,1))std::this_thread::yield();}});
    for(unsigned i=0;i<100000;++i){float p[2];while(!r->read(p,1))std::this_thread::yield();assert(p[0]==float(i) && p[1]==-float(i));}producer.join();
    auto h=std::make_unique<Host>();h->playback=true;float silence[256];
    Host::callback(nullptr,silence,128,nullptr,0,h.get());assert(h->output_underflows==0);
    h->output.write(pcm.data(),2048);
    for(int i=0;i<16;++i)Host::callback(nullptr,silence,128,nullptr,0,h.get());
    assert(h->played==2048 && h->output_underflows==0);
    Host::callback(nullptr,silence,128,nullptr,0,h.get());assert(h->output_underflows==128);
    Host::callback(nullptr,silence,128,nullptr,0,h.get());assert(h->output_underflows==256);
    for(float f:silence)assert(f==0);
    h->recording=true;
    Host::callback(silence,nullptr,128,nullptr,paInputOverflow,h.get());assert(h->captured==128 && h->driver_flags==paInputOverflow);
}
