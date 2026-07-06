/**
 * fetch-doppler-secret.js
 *
 * Unlocks a password-protected Doppler Share link (share.doppler.com) using
 * a headless browser, then reads the decrypted secret out of the page's
 * `<textarea class="secret ...">` element once it's populated.
 *
 * Why a headless browser (Playwright) instead of a plain HTTP scrape?
 * Doppler Share decrypts the secret client-side in the browser (AES-GCM,
 * key derived from the passphrase via PBKDF2). The textarea is empty until
 * that JS runs, so a simple `curl`/`fetch` of the HTML will never contain
 * the secret value — you need something that actually executes the page's
 * JavaScript, submits the password form, and waits for the DOM to update.
 *
 * Required environment variables (set these as GitHub Actions secrets,
 * never hardcode them):
 *   DOPPLER_SHARE_URL      - the share.doppler.com/s/... link
 *   DOPPLER_SHARE_PASSWORD - the passphrase/password for that link
 *
 * Output:
 *   Prints the secret to stdout is intentionally AVOIDED. Instead this
 *   script writes it to $GITHUB_OUTPUT (masked) so it never appears in
 *   plain text in the Actions log.
 */

const { chromium } = require('playwright');
const fs = require('fs');

async function main() {
  const shareUrl = process.env.DOPPLER_SHARE_URL;
  const password = process.env.DOPPLER_SHARE_PASSWORD;

  if (!shareUrl || !password) {
    console.error('Missing DOPPLER_SHARE_URL or DOPPLER_SHARE_PASSWORD env vars.');
    process.exit(1);
  }

  // Mask the password immediately in case Playwright ever logs args/errors
  if (process.env.GITHUB_ACTIONS) {
    console.log(`::add-mask::${password}`);
  }

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    await page.goto(shareUrl, { waitUntil: 'networkidle' });

    // Doppler's password-unlock form. Selector names can change over time —
    // inspect the live page and adjust if this breaks.
    const passwordInput = page.locator('input[type="password"]');
    await passwordInput.waitFor({ state: 'visible', timeout: 15000 });
    await passwordInput.fill(password);

    // Submit — either pressing Enter or clicking the visible submit/view button works.
    await passwordInput.press('Enter');

    // Wait for the secret textarea to be populated (not just present).
    const secretBox = page.locator('div.secret-container textarea.secret');
    await secretBox.waitFor({ state: 'visible', timeout: 15000 });

    // Poll until the textarea actually has a non-empty value, since the
    // decrypt-and-fill happens asynchronously after submit.
    let secretValue = '';
    for (let i = 0; i < 20; i++) {
      secretValue = await secretBox.inputValue();
      if (secretValue && secretValue.length > 0) break;
      await page.waitForTimeout(500);
    }

    if (!secretValue) {
      throw new Error('Timed out waiting for secret to decrypt/populate.');
    }

    // Mask again now that we know the real value, then emit it as a
    // step output rather than printing it directly.
    if (process.env.GITHUB_ACTIONS) {
      console.log(`::add-mask::${secretValue}`);
      const githubOutput = process.env.GITHUB_OUTPUT;
      fs.appendFileSync(githubOutput, `secret=${secretValue}\n`);
    } else {
      // Local/manual run fallback
      console.log('Secret retrieved (not printed). Length:', secretValue.length);
    }
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error('Failed to fetch Doppler share secret:', err.message);
  process.exit(1);
});
