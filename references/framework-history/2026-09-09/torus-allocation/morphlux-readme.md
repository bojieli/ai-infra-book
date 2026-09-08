# Morphlux
Morphlux is a server-scale programmable photonic fabric interconnecting accelerators within servers. MorphMGR is the service for resource scheduling and management.

## Development
```
python -m venv env
source env/bin/activate
pip install -r requirements.txt
pip install -e .

# gurobi license
export LICENSEID=<LICENSEID>
export WLSACCESSID=<ACCESSID>
export WLSSECRET=<SECRET>

```

## Testing
```
pytest tests/
```
