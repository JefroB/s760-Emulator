import {describe,it,expect,vi} from 'vitest';
import {S760BridgeClient, SurfaceId, type EmbeddedBridgeTransport} from './S760BridgeClient';

class Channel implements EmbeddedBridgeTransport {
  listeners=new Set<(event:{data:unknown})=>void>();
  postMessage=vi.fn();
  addEventListener(_type:'message',listener:(event:{data:unknown})=>void){this.listeners.add(listener);}
  removeEventListener(_type:'message',listener:(event:{data:unknown})=>void){this.listeners.delete(listener);}
  emit(data:unknown){for(const listener of this.listeners) listener({data});}
}

describe('embedded editor channel',()=>{
  it('sends canonical controls without opening a socket and detaches on close',()=>{
    const channel=new Channel(), socket=vi.fn();
    const client=new S760BridgeClient({embeddedTransport:channel,webSocketFactory:socket});
    client.connect();client.connect();
    expect(channel.listeners.size).toBe(1);expect(socket).not.toHaveBeenCalled();
    client.sendButtonPress('MODE');
    expect(JSON.parse(channel.postMessage.mock.calls[0][0])).toEqual({type:'BUTTON_PRESS',payload:{id:'MODE'}});
    client.disconnect();expect(channel.listeners.size).toBe(0);
    client.sendButtonPress('MODE');expect(channel.postMessage).toHaveBeenCalledTimes(1);
    client.connect();expect(client.isConnected()).toBe(true);
    client.dispose();expect(channel.listeners.size).toBe(0);
  });
  it('uses canonical frame decoding and rejects malformed or oversized envelopes',()=>{
    const channel=new Channel(), client=new S760BridgeClient({embeddedTransport:channel});
    const frame=vi.fn();client.onFrame(SurfaceId.LCD,frame);client.connect();
    const bytes=String.fromCharCode(1,8,0,1,0,1,0x81);
    channel.emit({type:'S760_FRAME',base64:btoa(bytes)});
    expect(frame).toHaveBeenCalledTimes(1);
    expect(Array.from(frame.mock.calls[0][0].payload)).toEqual([0x81]);
    for(const base64 of ['%',btoa('bad'),'A'.repeat(1638409)]) channel.emit({type:'S760_FRAME',base64});
    expect(frame).toHaveBeenCalledTimes(1);
    client.dispose();channel.emit({type:'S760_FRAME',base64:btoa(bytes)});
    expect(frame).toHaveBeenCalledTimes(1);
  });
});
