# torchtree-bito

torchtree-bito is a package providing an interface to [BITO] for [torchtree]

## Dependencies
 - [torchtree]
 - [BITO]

## Installation

Instructions about installing BITO can be found on the [BITO] website.

### Get the source code
```bash
git clone https://github.com/4ment/torchtree-bito
cd torchtree-bito
```

### Install using pip
```bash
pip install .
```

## Check install
```bash
python -c "import bito"
```

```bash
torchtree --help
```

## Command line arguments
The torchtree-bito plugin adds these arguments to the torchtree CLI:

```bash
torchtree-cli advi --help
  ...
  --bito                use bito
  --bito_gpu            use GPU in bito/BEAGLE
  --bito_disable_sse    disable SSE in bito/BEAGLE
```

## Quick start
torchtree will approximate the posterior distribution of an unrooted tree with an HKY substitution model using variational 
```bash
torchtree examples/advi/fluA-HKY.json
```

The JSON file can be generated by providing an alignment and a tree to the torchtree CLI:
```bash
torchtree-cli advi -i foo.fa -t foo.tree -m HKY --bito > foo.json
```

[torchtree]: https://github.com/4ment/torchtree
[BITO]: https://github.com/phylovi/bito