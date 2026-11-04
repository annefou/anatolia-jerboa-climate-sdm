# `data/`: not used by this replication

The pipeline downloads into `work/` (not committed) and writes summary results to `results/`. The data sources, the
accounts each step needs (Copernicus Climate Data Store, Copernicus Marine, DestinE upgraded access) and how to set
them up are in the README, section **Install and run**. Accounts are read from your home directory or the
environment, never from the repository.
