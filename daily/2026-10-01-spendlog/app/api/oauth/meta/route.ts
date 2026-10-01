// /.well-known/oauth-authorization-server (rewritten here): the sign-in endpoints.
import { metadata } from '../../../../lib/oauth.ts';
import { originOf } from '../../../../lib/origin.ts';
export const dynamic = 'force-dynamic';
export function GET(req: Request) { return Response.json(metadata(originOf(req)).server, { headers: { 'Access-Control-Allow-Origin': '*' } }); }
