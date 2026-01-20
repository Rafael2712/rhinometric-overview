# Rhinometric WordPress Theme

## Summary
- Conversion-focused, WCAG 2.1 AA aligned marketing site
- i18n-ready with WordPress translation functions
- Download gating form with email delivery
- SEO meta tags per page + Open Graph

## Install
1. Copy the folder into `wp-content/themes/rhinometric-enterprise`.
2. Activate the theme in WordPress.
3. Create pages with these slugs:
   - `home` (set as Front Page)
   - `platform`
   - `observability-suite`
   - `on-prem`
   - `security`
   - `roadmap`
   - `download`
   - `thank-you`
   - `request-demo`
   - `contact`
4. Assign menus:
   - Primary menu: Home, Platform, Observability Suite, On-Prem, Security, Roadmap, Download, Request a demo, Contact
   - Footer menu: Platform, Security, Roadmap, Contact

## Language setup (EN/ES)
- EN is the default language.
- ES is enabled via a language switcher that persists user choice in a cookie.
- If you later install Polylang, the header switcher will use it automatically.

## Download flow
- Form stores leads in WP Admin (Download Leads).
- Email sends a download link from Settings option `rinometry_download_url`.
- Lead notification goes to `rinometry_lead_recipient` (default: rafael.canelon@rhinometric.com).
- Update the link in WP Admin via `Settings -> General` using a custom option or set it via code.
- Leads can be exported via WP Admin → Tools → Rhinometric Leads Export.

## SEO
- Each page outputs meta description + Open Graph.
- Add a custom field `_rino_meta_description` per page for better copy.
- WordPress core sitemap is enabled by default at `/wp-sitemap.xml`.

## Assets
- Upload the official logo and screenshots into `assets/img/`:
   - logo-rhinometric.png (official logo, used in header + favicon)
   - logo-rhinometric.svg (fallback)
   - logo-rhinometric-alt.svg (optional alt version with orange accent)
   - hero-visual.png (optional)
   - product-dashboard.png
   - product-logs.png
   - product-traces.png
   - product-alerts.png
   - integrations-grid.png (optional)
- The theme ships with SVG placeholders. Replace them with PNGs when ready.

## Notes
- The theme does not touch Rhinometric core services.
- Update placeholder content in Thank You page when installation docs are ready.

## i18n validation
- Before committing translations, run: `msgfmt -c -o /dev/null web/wordpress-theme-rinometry/languages/*.po`
- Avoid duplicate `msgid` entries; keep a single definition per string.

## TODO (future-safe alignment)
- The theme folder and text domain use `rinometry`, while the product name is “Rhinometric”.
- Plan a dedicated phase to align folder name, theme slug, and textdomain without breaking translations.
