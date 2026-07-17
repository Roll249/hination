#!/bin/bash
# HINATION Hourly Scheduler
# Pulls new data, retrains, and updates dashboard every hour

cd /home/khang/khang_lab/hination-hackathon

echo "================================================================"
echo "  HINATION HOURLY SCHEDULER"
echo "  - Pull data every 1 hour from GFS Seamless"
echo "  - Retrain hourly hybrid ensemble"
echo "  - Update dashboard automatically"
echo "================================================================"

# Run scheduler in foreground
# The script will:
# 1. Run immediately on start
# 2. Then every 1 hour
# 3. Log everything to logs/hourly_scheduler.log

mkdir -p logs
exec python model/hourly_pipeline.py schedule 2>&1 | tee -a logs/hourly_scheduler.log