/**
 * @jest-environment node
 */
const { parseCommentary } = require('./v1-commentary');

// Hadith 3 in v1, as riyad_salheen.db stores it.
const HADITH_3 = `<p0>لغة الحديث</p0> :
<p1>بعد</p1> <p1>الفتح</p1> : أي بعد فتح مكة ، وكان فتحها سنة ثمان بعد الهجرة .
<p1>جهاد</p1> : محاربة الكفار .
<p0>أفاد الحديث :</p0>
<bullet> إذا صارت البلد دار إسلام لم تجب الهجرة منها إلى غيرها
<bullet> تبقى الهجرة واجبة من الأماكن التي لا يتيسر للمسلم إقامة أمر دينه فيها.
`;

test('splits word meanings and benefits', () => {
  expect(parseCommentary(HADITH_3)).toEqual({
    meanings: [
      { term: 'بعد الفتح', meaning: 'أي بعد فتح مكة ، وكان فتحها سنة ثمان بعد الهجرة .' },
      { term: 'جهاد', meaning: 'محاربة الكفار .' },
    ],
    benefits: [
      'إذا صارت البلد دار إسلام لم تجب الهجرة منها إلى غيرها',
      'تبقى الهجرة واجبة من الأماكن التي لا يتيسر للمسلم إقامة أمر دينه فيها.',
    ],
  });
});

test('a colon inside the marked word, and a heading split over two tags', () => {
  const { meanings } = parseCommentary('<p0>لغة</p0> <p0>الحديث</p0> <p1>:</p1>\n<p1>الحفص :</p1> الأسد .');
  expect(meanings).toEqual([{ term: 'الحفص', meaning: 'الأسد .' }]);
});

test('word meanings written as bullets, as from v1 hadith 113 on', () => {
  const { meanings } = parseCommentary(
    '<p0>لغة الحديث:</p0>\n<bullet> <p1>أشياخ:</p1> جمع شيخ.\n<bullet> <p1>يتأول القرآن</p1> : يخصص عمومه.',
  );
  expect(meanings).toEqual([
    { term: 'أشياخ', meaning: 'جمع شيخ.' },
    { term: 'يتأول القرآن', meaning: 'يخصص عمومه.' },
  ]);
});

test('lines that go on from the one before', () => {
  const { meanings, benefits } = parseCommentary(
    '<p0>لغة الحديث</p0>\n<p1>جهاد</p1> : محاربة\nالكفار .\n<p0>أفاد الحديث</p0>\n<bullet> أولى\nتتمة الأولى',
  );
  expect(meanings).toEqual([{ term: 'جهاد', meaning: 'محاربة الكفار .' }]);
  expect(benefits).toEqual(['أولى تتمة الأولى']);
});

test('several benefits on one line, and a note', () => {
  const { benefits } = parseCommentary('<p0>أفاد الحديث</p0>\n<bullet> أولى <bullet> ثانية\n<p0>تنبيه :</p0> ملاحظة');
  expect(benefits).toEqual(['أولى', 'ثانية', 'تنبيه : ملاحظة']);
});

test('no commentary', () => {
  expect(parseCommentary('')).toEqual({ meanings: [], benefits: [] });
  expect(parseCommentary(null)).toEqual({ meanings: [], benefits: [] });
});

test('words not marked, where a commentary marks none', () => {
  const { meanings } = parseCommentary('<p0>لغة</p0> <p0>الحديث</p0> :\nاتق الله : أي اجعل بينك وبين عقاب الله وقاية.\nرد: مردود.');
  expect(meanings).toEqual([
    { term: 'اتق الله', meaning: 'أي اجعل بينك وبين عقاب الله وقاية.' },
    { term: 'رد', meaning: 'مردود.' },
  ]);
});

test('an unmarked «… : …» goes on with the meaning before it, where words are marked', () => {
  const { meanings } = parseCommentary('<p0>لغة الحديث</p0>\n<p1>ولياً</p1> : القريب من الله.\nقال تعالى : آية.');
  expect(meanings).toEqual([{ term: 'ولياً', meaning: 'القريب من الله. قال تعالى : آية.' }]);
});

test('a verse marked <p0> inside a meaning is not a heading', () => {
  const { meanings, benefits } = parseCommentary(
    '<p0>لغة الحديث :</p0>\n<bullet> <p1>ولياً</p1> : القريب، قال تعالى : <p0>{ أَلَا إِنَّ أَوْلِيَاءَ اللَّهِ }</p0>\n<bullet> <p1>كنت سمعه</p1> : أي حافظاً لسمعه.\n<p0>أفاد الحديث</p0>\n<bullet> فائدة',
  );
  expect(meanings.map((meaning) => meaning.term)).toEqual(['ولياً', 'كنت سمعه']);
  expect(meanings[0].meaning).toContain('أَلَا إِنَّ أَوْلِيَاءَ اللَّهِ');
  expect(benefits).toEqual(['فائدة']);
});

test('benefits written as a paragraph, with no bullet', () => {
  const { benefits } = parseCommentary('<p0>أفاد الحديث :</p0>\nأن الأعمال إنما يعتد بها بحسب النيات.\nتتمة.');
  expect(benefits).toEqual(['أن الأعمال إنما يعتد بها بحسب النيات. تتمة.']);
});

test('text before a line\'s first bullet goes on with the item before it', () => {
  const sharh = [
    '<p0>لغة الحديث</p0>',
    '<bullet> <p1>الحفص:</p1> الأسد',
    'الضاري <bullet> <p1>جهاد:</p1> محاربة الكفار',
    '<p0>أفاد الحديث</p0>',
    '<bullet> الأولى',
    'تتمتها <bullet> الثانية',
  ].join('\n');
  expect(parseCommentary(sharh)).toEqual({
    meanings: [
      { term: 'الحفص', meaning: 'الأسد الضاري' },
      { term: 'جهاد', meaning: 'محاربة الكفار' },
    ],
    benefits: ['الأولى تتمتها', 'الثانية'],
  });
});
