# Add ub_scope to .topics imports in cli.py.
# Insert parser alongside other --inputs calculators:
ub = sub.add_parser('ub-scope', help='Eight-card capacity and declared one/two-server communication budget; not historical UB performance')
ub.add_argument('--inputs', type=Path)
ub.add_argument('--format', choices=('json','md'), default='json')
ub.add_argument('--output', type=Path)
# Insert dispatch in main's elif chain:
# elif args.command == 'ub-scope':
#     result = ub_scope.calculate(**(json.loads(args.inputs.read_text()) if args.inputs else {}))
