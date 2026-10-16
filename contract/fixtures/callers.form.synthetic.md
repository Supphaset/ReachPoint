# Synthetic caller forms

[callers.form.synthetic.json](callers.form.synthetic.json) contains six examples with exactly the fields shown by `/callers`: required phone number, food/evacuation type and Google Maps link; optional people details and situation details. Household counts, medication needs, water and access descriptions are caller text. Unused legacy structured fields remain unknown (`null`). No address, coordinates, transport, emergency level, prep summary or approval is supplied as a review result.

All households, place names and circumstances are fictional. The shared `0000000000` phone is a placeholder. Maps links contain explicit example pins around the demo geography, not verified household addresses or safe routes. Labels beginning with “Synthetic” identify examples; they are not provider-verified postal addresses.

The scenarios cover routine supplies, rising water at the last refuge, reported unresponsiveness, assisted evacuation, omitted optional information and hazardous access. They provide input variation rather than preset classifications. Normal AI review runs only when enabled on the server, and human approval remains separate.

Append the examples to a running local server, preserving existing requests:

```bash
python3 scripts/seed_callers.py --base-url http://127.0.0.1:8768
```

The script uses the same session and form submission endpoints as the UI. It skips an example only when all five fields already match; the shared phone never merges distinct requests. Rerunning skips examples already saved. It does not reset the demo or change existing records. Run a single seed process at a time.
