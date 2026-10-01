export const CONTACT = process.env.SPENDLOG_CONTACT || '';
export const contactLink = () => (CONTACT.includes('@') && !CONTACT.startsWith('http') ? `mailto:${CONTACT}` : CONTACT);
