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
- Install a multilingual plugin (recommended: Polylang).
- Add English as default language.
- Add Spanish language and translate each page.
- The header language switcher will use the plugin automatically.

## Download flow
- Form stores leads in WP Admin (Download Leads).
- Email sends a download link from Settings option `rinometry_download_url`.
- Lead notification goes to `rinometry_lead_recipient` (default: rafael.canelon@rhinometric.com).
- Update the link in WP Admin via `Settings -> General` using a custom option or set it via code.

## SEO
- Each page outputs meta description + Open Graph.
- Add a custom field `_rino_meta_description` per page for better copy.
- WordPress core sitemap is enabled by default at `/wp-sitemap.xml`.

## Assets
- Upload your logo and screenshots into `assets/img/`:
   - logo-rhinometric.svg
   - hero-illustration.svg
   - product-dashboard.svg
   - product-logs.svg
   - product-traces.svg
   - product-alerts.svg
   - integration-otel.svg
   - integration-prometheus.svg
   - integration-logging.svg

## Notes
- The theme does not touch Rhinometric core services.
- Update placeholder content in Thank You page when installation docs are ready.
