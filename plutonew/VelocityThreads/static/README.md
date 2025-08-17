# Static Assets

This folder contains static assets for the VelocityThreads e-commerce application.

## Hero Banner Image
Place the hero banner image as `hero-banner.jpeg` in the `static/images/` folder.

The image will be used as a full-screen background in the hero section with:
- Background-size: cover
- Background-position: center
- Dark overlay: rgba(0, 0, 0, 0.45) for text readability

The image should be:
- High resolution (recommended: 1920x1080px or larger)
- Named: `hero-banner.jpeg`
- Format: JPEG
- Optimized for web (file size under 2MB)
- Placed in: `static/images/hero-banner.jpeg`

## PLUTO Logo
Place the PLUTO logo as `pluto-logo.png` in the `static/images/` folder.

The logo will be used in the navigation bar with:
- Height: 40px (desktop), 35px (tablet), 30px (mobile)
- Max-width: 120px (desktop), 100px (tablet), 80px (mobile)
- Hover effect: subtle scale animation
- Fallback: Text "PLUTO" if image fails to load

The logo should be:
- High quality PNG with transparent background
- Named: `pluto-logo.png`
- Format: PNG (recommended for logos)
- Optimized for web (file size under 200KB)
- Placed in: `static/images/pluto-logo.png`

## Image Structure
```
static/
├── images/
│   ├── hero-banner.jpeg    # Main hero background image
│   └── pluto-logo.png      # PLUTO logo for navigation
└── pluto_fallback.webp     # Fallback image (if needed)
```

## Fallback Image
A fallback image `pluto_fallback.webp` is already provided from the existing PLUTO collection assets.

## Alternative
If you don't have the hero banner image or logo, you can use any of the existing images from the VelocityThreads/attached_assets folder by copying them here and updating the filename in the templates.
