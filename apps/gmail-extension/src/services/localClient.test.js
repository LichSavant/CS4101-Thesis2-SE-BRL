import {afterEach,expect,it,vi} from 'vitest';
let client;
class FakeWorker{
  static instances=[];
  constructor(){FakeWorker.instances.push(this);this.postMessage=vi.fn();this.terminate=vi.fn();}
  emit(data){this.onmessage({data});}
}
async function setup(get=vi.fn().mockResolvedValue({processingMode:'local'})){
  vi.stubGlobal('Worker',FakeWorker);vi.stubGlobal('chrome',{storage:{local:{get}}});
  client=await import('../../local/client.mjs');return get;
}
afterEach(()=>{client?.unload();client=null;FakeWorker.instances=[];vi.unstubAllGlobals();vi.resetModules();});
it('does not post or retain a stale RPC when unloaded during preference access',async()=>{
  let resolve;await setup(vi.fn(()=>new Promise(r=>{resolve=r;})));
  const pending=client.call('status').catch(e=>e);client.unload();resolve({processingMode:'local'});
  expect((await pending).message).toMatch(/stopped/);expect(FakeWorker.instances[0].postMessage).not.toHaveBeenCalled();
});
it('an old cancelled preference read cannot release a newer operation lock',async()=>{
  let resolveOld;const get=vi.fn().mockImplementationOnce(()=>new Promise(r=>{resolveOld=r;})).mockResolvedValue({processingMode:'local'});await setup(get);
  const old=client.call('status').catch(e=>e);client.unload();const fresh=client.call('status');await Promise.resolve();
  resolveOld({processingMode:'local'});await old;await expect(client.call('status')).rejects.toThrow(/already active/);
  const worker=FakeWorker.instances[1],id=worker.postMessage.mock.calls[0][0].id;worker.emit({id,ok:true,result:{installed:false}});expect(await fresh).toEqual({installed:false});
});
it('progress does not resolve the operation or allow duplicate queued work',async()=>{
  await setup();const progress=vi.fn(),pending=client.call('install',{},progress);await Promise.resolve();const worker=FakeWorker.instances[0],id=worker.postMessage.mock.calls[0][0].id;
  worker.emit({id,progress:{stage:'hashing',step:2,total:4}});expect(progress).toHaveBeenCalledWith({stage:'hashing',step:2,total:4});await expect(client.call('status')).rejects.toThrow(/already active/);
  worker.emit({id,ok:true,result:{installed:true}});expect((await pending).installed).toBe(true);
});

it('recovers when worker construction fails without retaining the busy lock',async()=>{
  await setup();vi.stubGlobal('Worker',class{constructor(){throw Error('denied');}});
  await expect(client.call('status')).rejects.toThrow(/worker unavailable/);
  vi.stubGlobal('Worker',FakeWorker);const pending=client.call('status');await Promise.resolve();
  const worker=FakeWorker.instances[0],id=worker.postMessage.mock.calls[0][0].id;
  worker.emit({id,ok:true,result:{installed:false}});expect(await pending).toEqual({installed:false});
});
it('ignores delayed errors from a terminated worker after explicit recovery',async()=>{
  await setup();const oldCall=client.call('status').catch(e=>e);await Promise.resolve();const old=FakeWorker.instances[0];
  client.unload();await oldCall;const fresh=client.call('status');await Promise.resolve();const worker=FakeWorker.instances[1];
  old.onerror();old.onmessageerror();expect(worker.terminate).not.toHaveBeenCalled();
  const id=worker.postMessage.mock.calls[0][0].id;worker.emit({id,ok:true,result:{installed:true}});expect((await fresh).installed).toBe(true);
});
it('fails closed on malformed worker messages and permits explicit restart',async()=>{
  await setup();const pending=client.call('status').catch(e=>e);await Promise.resolve();const worker=FakeWorker.instances[0];
  worker.onmessageerror();expect((await pending).message).toMatch(/stopped/);expect(worker.terminate).toHaveBeenCalled();
});
