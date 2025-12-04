#!/bin/bash

# Launch with: bash launch_2022.sh 2>&1 | tee output_2022.log
# Exit on error
set -e

echo "[1/6] Running make_histograms.py..."
python3 make_histograms.py configurations/config_2022.yaml

echo "[2/6] Entering directory Trota_TopSF_2022/BestTopMixed_mass/"
cd Trota_TopSF_2022/BestTopMixed_mass/

echo "[3/6] Sourcing combine_script.sh..."
source combine_script.sh

echo "[4/6] Running MultiDimFit..."
combine -M MultiDimFit workspace_pt400to600.root --redefineSignalPOIs SF_topmatched

echo "[5/6] Running FitDiagnostics..."
combine -M FitDiagnostics workspace_pt400to600.root \
    --redefineSignalPOIs SF_topmatched \
    --saveShapes \
    --saveWithUncertainties \
    --name _pt400to600

echo "[6/6] Returning to top directory and plotting histograms..."
cd ../../
python3 plot_histograms.py configurations/plot_2022.yaml

echo "ALL DONE."