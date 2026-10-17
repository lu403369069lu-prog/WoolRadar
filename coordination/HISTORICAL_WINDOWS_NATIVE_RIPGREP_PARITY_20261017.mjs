// Standalone offline native-platform SAM source-policy/ripgrep parity acceptance.
// From the frozen historical PR15 HEAD, no production write or network access.
import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { mkdtemp, mkdir, readFile, realpath, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const FROZEN_SAM_HEAD = '82bf36efa90cced8dafb56502812eb49f40515f3';
const FROZEN_SOURCE_BLOB = '0cb6ead5e4764aa8b7364ba92d3137b0b8171f5b';
const FILES = ['secret.txt','Secret.txt','notes.md','notes.txt','dir/a.txt','dir/a.md',
  'dir/deep/b.txt','dir/deep/b.md','private/a.txt','PRIVATE/a.txt',
  'lib/file.test.ts','lib/file.ts','src/Pascal.TcPOU','src/VAR.TcPOU',
  'src/axis_1.txt','src/axis_a.txt','docs/log1.md','docs/logA.md',
  'tmp/build.log','tmp/deep/build.log','misc/a.ts','misc/A.TS'];
const PATTERNS = ['secret.txt','Secret.txt','*.txt','*.md','*.ts','/dir/a.txt',
  'dir/a.txt','dir/**','/private/**','private/**','private','**/private/**',
  'src/*.TcPOU','src/axis_?.txt','src/axis_[0-9].txt','src/axis_[a-z].txt',
  'src/{axis_a,axis_1}.txt','**/*.txt','**/a.txt','**/build.log',
  '*.log','/tmp','**/tmp','/[Pp]rivate/**','/src/{Pascal,VAR}.TcPOU',
  'dir/deep/*.txt'];

function requireSuccessful(program, args, cwd) {
  const r = spawnSync(program, args, {cwd, encoding:'utf8', timeout:15000});
  assert.equal(r.error, undefined, program + ' is required: ' + r.error);
  assert.equal(r.status, 0, program + ' ' + args.join(' ') + ': ' + r.stderr);
  return r.stdout.trim();
}

test('native Windows or POSIX rg glob semantics match actual frozen SAM source-policy', async t => {
  const supplied = process.env.SAM_CHECKOUT_ROOT;
  assert.ok(supplied, 'Set SAM_CHECKOUT_ROOT to a disposable clean YinQieJi checkout');
  const root = await realpath(resolve(supplied));
  assert.equal(await realpath(requireSuccessful('git', ['rev-parse','--show-toplevel'], root)),root,
    'SAM_CHECKOUT_ROOT must be the git worktree root');
  assert.equal(requireSuccessful('git', ['rev-parse','HEAD'],root), FROZEN_SAM_HEAD,
    'Frozen PR15 SHA mismatch; stop and review new revision');
  assert.equal(requireSuccessful('git', ['status','--porcelain'],root),'',
    'Dirty source tree cannot produce clean acceptance');
  const source = join(root,'SAM','snapshot','src','source-policy.ts');
  const bytes = await readFile(source);
  const blob = createHash('sha1').update(Buffer.concat([
    Buffer.from('blob ' + bytes.length + '\0','utf8'),bytes])).digest('hex');
  assert.equal(blob,FROZEN_SOURCE_BLOB,'source-policy.ts exact Git blob changed');
  const { isExcluded } = await import(pathToFileURL(source).href);
  assert.equal(typeof isExcluded,'function','missing actual exported isExcluded');
  requireSuccessful('rg',['--version'],root);

  const temporary = await mkdtemp(join(tmpdir(),'sam-native-rg-'));
  t.after(async () => { await rm(temporary,{recursive:true,force:true}); });
  for (const relative of FILES) {
    await mkdir(dirname(join(temporary,relative)),{recursive:true});
    await writeFile(join(temporary,relative),'synthetic nonprivate fixture\n','utf8');
  }
  let compared=0;
  for (const pattern of PATTERNS) {
    const r = spawnSync('rg',['--files','--hidden','--no-ignore','-g','!'+pattern],
      {cwd:temporary,encoding:'utf8',timeout:15000});
    assert.equal(r.error,undefined,'rg spawn: ' + r.error);
    assert.ok(r.status===0||r.status===1,'rg failed on ' + pattern + ': ' + r.stderr);
    const allowed = new Set(r.stdout.trim().split(/\r?\n/).filter(Boolean)
      .map(s=>s.replaceAll('\\','/')));
    for (const rel of FILES) {
      const actual = isExcluded({path:temporary,exclude_patterns:[pattern]},join(temporary,rel));
      const expected = !allowed.has(rel);
      assert.equal(actual,expected,'platform ' + process.platform + ', glob ' + pattern + ', path ' + rel);
      compared++;
    }
  }
  assert.equal(compared,572);
});
