"""Shared reporting policy: a historical catalogue is not measured coverage."""
from pathlib import Path

# Reviewed assertions, not a list of passing results or whole-feature mappings.
# Keep a selector so existence alone cannot silently qualify another test file.
EVIDENCE = (
    ('Image bytes', 'tests/test_image_invariants.py::test_banner_tag_present',
     'Checks the banner bytes at one disk-image offset.',
     'Does not execute the bootloader or validate a save/load workflow.'),
    ('Static source', 'tests/test_mame_invariants.py::test_mame_driver_contains_mcs96_cpu',
     'Checks CPU configuration and address strings in driver source.',
     'Does not execute CPU instructions or establish interrupt behavior.'),
    ('React component', 'google-ui/src/components/NativePanelControls.test.tsx::routes Value wheel and keyboard steps through the encoder rather than S1/S2',
     'Renders the Value control and asserts DIAL_DELTA commands through mocked transport.',
     'Does not execute MAME, prove a firmware value changed, or establish hardware parity.'),
)


def cell(value):
    return str(value).replace('|', '&#124;').replace('\n', ' ')


def write_report(destination, title, sections):
    """sections: (heading, [(historical item name, historical context), ...])."""
    count = sum(len(rows) for _, rows in sections)
    lines = [
        '# ' + title, '',
        '## Unverified inventory', '',
        'This historical catalogue is a research checklist. Its item names and contexts',
        '(including addresses and manual pages) have not been individually revalidated.',
        'They are not verified binary mappings, component ownership, implementation',
        'status, or test results. Earlier automatic Tested badges and broad citations',
        'have been removed because they did not establish the behavior of each row.', '',
        f'**Catalogue entries:** {count}. **Individually qualified rows in this inventory:** 0.',
        '**No coverage percentage** is reported: neither a verified feature denominator',
        'nor an assertion-to-feature mapping has been established. This does not mean',
        'the project has no tests or working features.', '',
        '## Reviewed test evidence by layer', '',
        'These are examples of what the actual assertions establish, not coverage of',
        'the inventory below. React Vitest and Playwright suites exist. This generator',
        'does not run tests or infer a passing result from a test file existing.', '',
        '| Layer | Test selector | Assertion scope | Limit |',
        '| --- | --- | --- | --- |',
    ]
    for layer, reference, assertion, limitation in EVIDENCE:
        path = reference.split('::', 1)[0]
        lines.append(f'| {layer} | [{cell(reference)}](../{path}) | {assertion} | {limitation} |')
    lines += [
        '', 'For qualified native runtime, host and hardware results, use the',
        '[testing guide](condensed/08-testing-coverage-and-verification.md),',
        '[completion roadmap](COMPLETION_ROADMAP.md) and their dated validation records.',
        'Python peripheral mirrors and offline DSP tests are model evidence. A Lua',
        'completion flag or screenshot file alone is not a firmware workflow assertion.',
        'Hardware parity requires matched physical captures and stated tolerances.', '',
    ]
    for heading, rows in sections:
        lines += ['## ' + heading, '',
                  '| Historical item | Historical context (unverified) | Qualification |',
                  '| --- | --- | --- |']
        for name, context in rows:
            lines.append(f'| {cell(name)} | {cell(context)} | Unverified |')
        lines.append('')
    lines += ['## Promotion requirements', '',
              'Before qualifying an inventory row, record the current owner, a specific',
              'test selector, the assertion that exercises that behavior, a dated run',
              'and its build/media identities, and the limits of the result. A passing',
              'model test must never qualify original firmware or physical hardware.', '']
    Path(destination).write_text('\n'.join(lines), encoding='utf-8')
