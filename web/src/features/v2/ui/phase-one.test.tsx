import { renderToStaticMarkup } from "react-dom/server";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";
import { CopilotAnswer } from "./Answer";
import { buildTraceLines, readerLabel } from "./trace";
import type { FeedItem, Activity } from "../api";
describe('copilot answer', () => {
  it('renders bold and zone/household citations as route links, including bold citations', () => {
    const html = renderToStaticMarkup(<MemoryRouter>
      <CopilotAnswer text={'Go to **[D12] first**. Pick up [HH135].'} />
    </MemoryRouter>);
    expect(html).toContain('<strong><a href="/v/zone/D12">[D12]</a> first</strong>');
    expect(html).toContain('href="/v/case/HH135"');
  });
  it('escapes markup and leaves unrelated bracketed text alone', () => {
    const html = renderToStaticMarkup(<MemoryRouter>
      <CopilotAnswer text={'<script>bad</script> [unknown]'} />
    </MemoryRouter>);
    expect(html).toContain('&lt;script&gt;');
    expect(html).not.toContain('<script>');
    expect(html).toContain('[unknown]');
  });
});
const item: FeedItem = { id: 'M1', atH: 10, at: '21 Nov 16:00', channel: 'chat', source: 'family', text: '', householdId: 'HH1', zoneId: 'D12', how: 'Merged into existing household', tags: [], facts: [{ field: 'people', value: 3, quote: 'อยู่กัน 3 คน' }], label: null, reader: 'gemini:test' };
const activity: Activity[] = [{ atH: 11, at: '17:00', agent: 'Planner', text: 'Plan recorded', tool: '' }, { atH: 9, at: '15:00', agent: 'Physics', text: 'Water updated', tool: '' }];
describe('trace builder', () => {
  it('preserves quoted evidence, gloss, provenance, rules and model/action lines in time order', () => {
    const lines = buildTraceLines([item], activity);
    expect(lines.map(candidate => candidate.who)).toEqual(['action', 'gemini', 'rules', 'physics']);
    expect(lines[1]).toMatchObject({ quote: 'อยู่กัน 3 คน', gloss: 'people: 3', to: '/v/case/HH1' });
    expect(lines[2].what).toBe(item.how);
  });
  it('filters future evidence during replay and labels fallback readers honestly', () => {
    expect(buildTraceLines([item], activity, 9).map(candidate => candidate.who)).toEqual(['physics']);
    expect(buildTraceLines([{ ...item, reader: 'rules' }], [])[0].who).toBe('rules');
    expect(readerLabel('gemini:reader')).toBe('Gemini');
    expect(readerLabel('rules')).toBe('Rules');
  });
});
