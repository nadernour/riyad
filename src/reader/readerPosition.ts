import { useCallback, useState } from 'react';

import { lastHadithRead } from './lastHadith';

// A hadith asked for by another screen (/?id=12).
export function askedHadith(param: string | undefined): number | null {
  const id = Number(param);
  return Number.isInteger(id) && id > 0 ? id : null;
}

export interface SearchHighlight {
  id: number;
  query: string;
}

interface Position {
  // The hadith the reader is on, or asked to go to; the screen keeps it within the hadith there are.
  requested: number;
  highlight: SearchHighlight | null;
}

function asked(params: { id?: string; q?: string }, fallback: () => number): Position {
  const id = askedHadith(params.id);
  return { requested: id ?? fallback(), highlight: id && params.q ? { id, query: params.q } : null };
}

// Where the reader is. It opens at the hadith a link or another screen asks for (/?id=12), or the last one read. A
// hadith asked for while it is open moves it there, during render, as React has state follow a prop; the screen then
// clears the id from the route, so asking for the same hadith again is a new id too. Asked for from search
// (/?id=12&q=…), the hadith shows where the query is in it, until the reader turns a page.
export function useReaderPosition(params: { id?: string; q?: string }) {
  const [askedFor, setAskedFor] = useState(params.id);
  const [position, setPosition] = useState(() => asked(params, lastHadithRead));
  let current = position;
  if (params.id !== askedFor) {
    setAskedFor(params.id);
    if (askedHadith(params.id)) {
      current = asked(params, () => position.requested);
      setPosition(current);
    }
  }
  // The reader turned a page, by a swipe or a screen reader's action.
  const turnTo = useCallback((requested: number) => setPosition({ requested, highlight: null }), []);
  return { ...current, turnTo };
}
