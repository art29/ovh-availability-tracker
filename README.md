# OVH Availability Tracker

Simple python script to track the various availabilities of dedicated servers from OVH.

## Sample use case
```bash
python3 main.py
```

## Edit cases
```python

# Update the name and code to any code you want
plan_codes: Dict[str, str] = {
    'KS-A': '24ska01',
}
    
# Update "bhs" to any data centers
avail = get_ovh_availability(plan_codes, datacenters=["bhs"])
```