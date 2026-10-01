// /.well-known/oauth-protected-resource (rewritten here): tells Claude where to sign in.
import { metadata } from '../../../../lib/oauth.ts';
import { originOf } from '../../../../lib/origin.ts';
export const dynamic = 'force-dynamic';
export function GET(req: Request) { return Response.json(metadata(originOf(req)).resource, { headers: { 'Access-Control-Allow-Origin': '*' } }); }
