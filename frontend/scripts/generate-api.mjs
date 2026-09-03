import { readFile, writeFile, mkdir } from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';

const output = new URL('../src/shared/api/generated.ts', import.meta.url);
const schema = new URL('../../openapi/internal-v1.yaml', import.meta.url);
const generated =
  '// Generated from openapi/internal-v1.yaml. Do not edit.\n' +
  astToString(await openapiTS(schema, { defaultNonNullable: false }));
if (process.argv.includes('--check')) {
  const current = await readFile(output, 'utf8').catch(() => '');
  if (current.replaceAll('\r\n', '\n') !== generated.replaceAll('\r\n', '\n')) {
    console.error('OpenAPI types are out of date. Run npm run api:generate.');
    process.exitCode = 1;
  } else {
    console.log('OpenAPI types match the canonical contract.');
  }
} else {
  await mkdir(new URL('../src/shared/api/', import.meta.url), { recursive: true });
  await writeFile(output, generated);
}
