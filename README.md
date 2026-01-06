# Circular-Economy
# Vienna Circular Electrification – Illustrative Model

This repository contains a small, scenario-based Python model developed to explore
electrification pathways, renewable energy expansion, and circular battery material
flows for the city of Vienna.

The model simulates annual electricity demand growth driven by electrification and
estimates the required expansion of renewable generation and battery storage.
A simple circular economy representation is included by accounting for battery
lifetimes, recycling rates, and primary material requirements.

The focus of this work is on comparing long-term scenarios and understanding
trade-offs between investment needs and CO₂ emissions, rather than producing
precise forecasts. All numerical values are illustrative and based on publicly
available Austrian and EU-level sources.

## Scenarios
- Vienna_Base: moderate electrification and renewable expansion
- Vienna_FastElectrification: faster demand growth with higher renewable targets
- Vienna_CircularPush: stronger emphasis on battery recycling and circularity

## Requirements
- Python 3
- numpy
- pandas

## How to run
```bash
pip install -r requirements.txt
python vienna_circular_electrification.py
