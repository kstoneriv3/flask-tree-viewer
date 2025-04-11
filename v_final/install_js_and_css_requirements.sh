#!/bin/bash
# Script: download_assets.sh
# Description: Downloads the required CSS and JS assets for the Job Dashboard app
# so that the app can run offline using local copies.

# Create directories for CSS and JS if they don't exist
mkdir -p static/css
mkdir -p static/js

# Download CSS files
echo "Downloading CSS files..."
wget -O static/css/bootswatch-cosmo.min.css "https://cdn.jsdelivr.net/npm/bootswatch@5.2.3/dist/cosmo/bootstrap.min.css" || { echo "Failed to download bootswatch-cosmo.min.css"; exit 1; }
wget -O static/css/jstree.default.min.css "https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/themes/default/style.min.css" || { echo "Failed to download jstree.default.min.css"; exit 1; }
wget -O static/css/github.min.css "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/styles/github.min.css" || { echo "Failed to download github.min.css"; exit 1; }
wget -O static/css/jquery-ui.css https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css || { echo "Failed to download jquery-ui.css"; exit 1; }


# Download JS files
echo "Downloading JavaScript files..."
wget -O static/js/jquery.min.js "https://cdnjs.cloudflare.com/ajax/libs/jquery/3.6.0/jquery.min.js" || { echo "Failed to download jquery.min.js"; exit 1; }
wget -O static/js/jquery-ui.min.js "https://code.jquery.com/ui/1.13.2/jquery-ui.min.js" || { echo "Failed to download jquery.min.js"; exit 1; }
wget -O static/js/bootstrap.bundle.min.js "https://cdn.jsdelivr.net/npm/bootstrap@5.2.3/dist/js/bootstrap.bundle.min.js" || { echo "Failed to download bootstrap.bundle.min.js"; exit 1; }
wget -O static/js/jstree.min.js "https://cdnjs.cloudflare.com/ajax/libs/jstree/3.3.12/jstree.min.js" || { echo "Failed to download jstree.min.js"; exit 1; }
wget -O static/js/highlight.min.js "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.7.0/highlight.min.js" || { echo "Failed to download highlight.min.js"; exit 1; }

# JQuery UI assets
wget -O static/css/throbber.gif https://code.jquery.com/ui/1.13.2/themes/base/images/throbber.gif
wget -O static/css/32px.png https://code.jquery.com/ui/1.13.2/themes/base/images/32px.png

echo "All assets downloaded successfully."
