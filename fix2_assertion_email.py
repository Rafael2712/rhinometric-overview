#!/usr/bin/env python3
# Phase 3 FIX-2: Assertion email notification

with open('/tmp/alert_rules.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the section where assertion alert is created
old_section = '''                db.add(event)
                fired += 1
                logger.info(
                    "[Assertions] Fired assertion-failure alert for %s: %s",
                    entity_name, summary_text[:200],
                )'''

new_section = '''                db.add(event)
                db.flush()  # Materialize event.id for email service
                
                # Phase 3 FIX-2: Send email notification for assertion failures
                try:
                    from services.alert_email_service import send_firing_notification
                    event.notification_sent_at = now
                    db.flush()
                    send_firing_notification(event, current_value=fail_count)
                    logger.info(
                        "[Assertions] Email notification triggered for %s",
                        entity_name
                    )
                except Exception as _email_err:
                    logger.warning(
                        "[Assertions] Email notification failed (non-fatal): %s",
                        _email_err
                    )
                
                fired += 1
                logger.info(
                    "[Assertions] Fired assertion-failure alert for %s: %s",
                    entity_name, summary_text[:200],
                )'''

if old_section in content:
    content = content.replace(old_section, new_section)
    
    with open('/tmp/alert_rules_fixed.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print('FIX-2 APPLIED: Assertion failures now send email notifications')
    print(f'File written to /tmp/alert_rules_fixed.py')
else:
    print('ERROR: Could not find target section')
    print('Searching for alternative pattern...')
    # Try with different whitespace
    if 'db.add(event)' in content and 'fired += 1' in content:
        print('Found db.add and fired += 1, but exact match failed')
        print('Manual inspection needed')
    exit(1)
