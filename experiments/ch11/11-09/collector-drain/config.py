def config(c,persistent):
 ext=f'  file_storage:\n    directory: {c / "storage"}\n    fsync: true\n' if persistent else ''
 storage='      storage: file_storage\n' if persistent else ''
 return f'''extensions:
  health_check:
    endpoint: 127.0.0.1:31333
{ext}receivers:
  otlp:
    protocols:
      http:
        endpoint: 127.0.0.1:31331
exporters:
  otlphttp:
    endpoint: http://127.0.0.1:31332
    encoding: json
    compression: none
    timeout: 1s
    retry_on_failure:
      enabled: true
      initial_interval: 200ms
      max_interval: 1s
      max_elapsed_time: 0s
    sending_queue:
      enabled: true
      num_consumers: 1
      queue_size: 100
{storage}service:
  extensions: [health_check{', file_storage' if persistent else ''}]
  telemetry:
    logs:
      level: debug
  pipelines:
    logs:
      receivers: [otlp]
      exporters: [otlphttp]
'''
