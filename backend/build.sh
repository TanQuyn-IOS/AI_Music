#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎨 Collecting static files with WhiteNoise..."
python manage.py collectstatic --no-input

echo "🗄️ Applying database migrations..."
python manage.py migrate --run-syncdb

echo "🌱 Seeding initial demo data..."
python seed_data.py || true

echo "✅ Build completed successfully!"
