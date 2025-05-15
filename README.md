# SUMO-RL

SUMO-RL provides a simple interface to instantiate Reinforcement Learning (RL) environments with [SUMO](https://github.com/eclipse/sumo) for Traffic Signal Control.

Goals of this repository:
- Provide a simple interface to work with Reinforcement Learning for Traffic Signal Control using SUMO
- Support Multiagent RL
- Easy customisation: state and reward definitions are easily modifiable

Warning: here for some reason `observation` and `state` are synonyms.

## Install

<!-- start install -->

### Install SUMO latest version:

```bash
sudo add-apt-repository ppa:sumo/stable
sudo apt-get update
sudo apt-get install sumo sumo-tools sumo-doc
```
Don't forget to set SUMO_HOME variable (default sumo installation path is /usr/share/sumo)
```bash
echo 'export SUMO_HOME="/usr/share/sumo"' >> ~/.bashrc
source ~/.bashrc
```
Important: for a huge performance boost (~8x) with Libsumo, you can declare the variable:
```bash
export LIBSUMO_AS_TRACI=1
```
Notice that you will not be able to run with sumo-gui or with multiple simulations in parallel if this is active ([more details](https://sumo.dlr.de/docs/Libsumo.html)).

### Install SUMO-RL

Stable release version is available through pip
```bash
pip install sumo-rl
```

Alternatively, you can install using the latest (unreleased) version
```bash
git clone https://github.com/LucasAlegre/sumo-rl
cd sumo-rl
pip install -e .
```

## Scenarios

### CELORIA

![map](./scenarios/celoria/map.png)

Layout:

| Axis | From | To |
| ---- | ---- | -- |
| main | J2 | J16 |
| side | J3 | J0 |
| side | J6 | J8 |
| side | J7 | J9 |
| side | J12 | J13 |
| side | J15 | J14 |

### BREDA

![map](./scenarios/breda/map.png)

Layout:

| Axis | From | To |
| ---- | ---- | -- |
| main | J0 | J3 |
| side | J4 | J5 |
| side | J6 | J7 |
