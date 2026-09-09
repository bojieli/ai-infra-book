import pathlib,os,difflib,json,hashlib
src=pathlib.Path(os.environ['VERLRL_SOURCE']);out=pathlib.Path(os.environ['VERLRL_ROOT'])/'patch';out.mkdir(exist_ok=True);records=[];diff=[]
changes={
'verl/workers/engine/fsdp/transformer_impl.py':[
 ('        assert self.optimizer_config.clip_grad is not None','        from observe import optimizer as _observe_optimizer\n        _observe_optimizer(self, "before")\n        assert self.optimizer_config.clip_grad is not None'),
 ('        return grad_norm.item()','        _observe_optimizer(self, "after")\n        return grad_norm.item()')],
'verl/trainer/ppo/ray_trainer.py':[
 ('                logger.log(data=metrics, step=self.global_steps)', '                from observe import metrics as _observe_metrics\n                _observe_metrics(metrics, self.global_steps)\n                logger.log(data=metrics, step=self.global_steps)'),
 ('            test_batch.meta_info["validate"] = True', '            test_batch.meta_info["validate"] = True\n            from observe import batch as _observe_validation\n            _observe_validation(test_batch, self.global_steps, stage="validation")'),
 ('                    # update critic\n','                    from observe import batch as _observe_batch\n                    _observe_batch(batch, self.global_steps)\n                    # update critic\n')],
'verl/workers/rollout/vllm_rollout/utils.py':[
 ('                            model.load_weights(param_updates)','                            model.load_weights(param_updates)\n                            from observe import receiver as _observe_receiver\n                            _observe_receiver(model, param_updates)'),
 ('ipc:///tmp/rl-colocate-zmq-', 'ipc://{os.environ[\'VERLRL_IPC\']}/rl-colocate-zmq-')],
'verl/workers/rollout/vllm_rollout/vllm_rollout.py':[
 ('        await sender.async_send_weights(weights)','        from observe import sender as _observe_sender\n        await sender.async_send_weights(_observe_sender(weights, global_steps))'),
 ('ipc:///tmp/rl-colocate-zmq-', 'ipc://{os.environ[\'VERLRL_IPC\']}/rl-colocate-zmq-')]
}
for rel,pairs in changes.items():
 p=src/rel;current=p.read_text();original=out/rel.replace('/','__')
 before=original.read_text() if original.exists() else current
 previous=json.loads((out/'sources.json').read_text()) if (out/'sources.json').exists() else []
 expected=next((x for x in previous if x['path']==rel),None)
 if expected:assert hashlib.sha256(current.encode()).hexdigest() in [expected['original_sha256'],expected['patched_sha256']],rel
 after=before
 for old,new in pairs:
  assert after.count(old)==1,(rel,old,after.count(old));after=after.replace(old,new)
 records.append(dict(path=rel,original_sha256=hashlib.sha256(before.encode()).hexdigest(),patched_sha256=hashlib.sha256(after.encode()).hexdigest()))
 diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel));(out/rel.replace('/','__')).write_text(before);p.write_text(after)
(out/'observations.diff').write_text(''.join(diff));(out/'sources.json').write_text(json.dumps(records,indent=2)+'\n')
