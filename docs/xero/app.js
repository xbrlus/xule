/* ============================================================
   XERO × NOTIFIER — app.js
   Uses Google OAuth 2.0 (implicit/token flow via GIS) +
   Gmail REST API to send email notifications.
   ============================================================ */

const RECIPIENT = 'david.tauriello@xbrl.us';
const GMAIL_SCOPE = 'https://www.googleapis.com/auth/gmail.send';

/* ── In-session state (never persisted) ── */
const creds = {
  googleClientId: '',
  xeroSecret: ''
};
const XERO_WEBHOOK_KEY = 'c88f3d6a-0ec4-4370-a35c-cfddd8fc58b5';
const XERO_CLIENT_ID = 'ADC67CDD91C24F16B509C99F184724CE';
const XERO_TENANT_ID = '8e1d07c3-9e3d-416c-b2e0-7e731cdaab80';

let googleAccessToken  = null;   // set after OAuth popup
let tokenExpiresAt     = 0;      // epoch ms

/* ── Initial mock event data ── */
let events = [
  { id: 1, vendor: 'Acme Corp',        amount: '$4,250.00',  invoiceNum: 'INV-2024-0891', status: 'sent',   time: '2 min ago' },
  { id: 2, vendor: 'TechSupplies Ltd', amount: '$12,800.00', invoiceNum: 'INV-2024-0887', status: 'sent',   time: '1 hr ago'  },
  { id: 3, vendor: 'Office Depot',     amount: '$340.50',    invoiceNum: 'INV-2024-0883', status: 'sent',   time: '3 hrs ago' },
];

/* ── Backend code snippet (shown in Code tab) ── */
const CODE_SNIPPET =
`// backend/webhook.js — Express webhook handler
// Sends email via Gmail API using a Google service account
const express    = require('express');
const crypto     = require('crypto');
const { google } = require('googleapis');

const app = express();

// Initialise Gmail client with a service account key file
// (or store an OAuth refresh token and use oauth2Client)
const auth  = new google.auth.GoogleAuth({
  keyFile: 'service-account-key.json',
  scopes: ['https://www.googleapis.com/auth/gmail.send'],
});
const gmail = google.gmail({ version: 'v1', auth });

app.post('/xero/webhook', express.raw({ type: '*/*' }), async (req, res) => {
  // 1. Verify Xero webhook signature using your Client Secret
  const sig  = req.headers['x-xero-signature'];
  const hash = crypto
    .createHmac('sha256', process.env.XERO_CLIENT_SECRET)
    .update(req.body)
    .digest('base64');

  if (hash !== sig) return res.status(401).send('Unauthorized');
  res.status(200).send(); // Acknowledge immediately

  // 2. Parse events
  const payload = JSON.parse(req.body);
  for (const event of payload.events) {
    if (
      event.eventCategory === 'INVOICE' &&
      event.eventType     === 'UPDATE'  &&
      event.resourceId
    ) {
      await checkAndNotify(event.resourceId);
    }
  }
});

async function checkAndNotify(invoiceId) {
  // 3. Fetch invoice details from Xero API
  const invoice = await xeroClient.accountingApi.getInvoice(
    process.env.XERO_TENANT_ID, invoiceId
  );
  const inv = invoice.body.invoices[0];

  // 4. Only notify for bills (AP) with status SUBMITTED
  if (inv.type !== 'ACCPAY' || inv.status !== 'SUBMITTED') return;

  // 5. Build RFC 2822 message and base64url-encode it
  const to      = '${RECIPIENT}';
  const subject = \`[Xero] Bill Submitted for Approval – \${inv.invoiceNumber}\`;
  const body    =
    \`Hello David,\\n\\n\` +
    \`A bill has been submitted for approval in Xero.\\n\\n\` +
    \`• Vendor:    \${inv.contact.name}\\n\` +
    \`• Invoice:   \${inv.invoiceNumber}\\n\` +
    \`• Amount:    \${inv.currencyCode} \${inv.amountDue.toFixed(2)}\\n\` +
    \`• Due Date:  \${inv.dueDate}\\n\` +
    \`• Submitted: \${new Date().toLocaleString()}\\n\\n\` +
    \`Review in Xero:\\n\` +
    \`https://go.xero.com/AccountsPayable/View.aspx?InvoiceID=\${inv.invoiceID}\\n\\n\` +
    \`— Automated Xero Notifier\`;

  const raw = Buffer.from(
    \`To: \${to}\\r\\nSubject: \${subject}\\r\\nContent-Type: text/plain; charset=utf-8\\r\\n\\r\\n\${body}\`
  ).toString('base64url');

  // 6. Send via Gmail API
  await gmail.users.messages.send({
    userId: 'me',
    requestBody: { raw }
  });
  console.log(\`Email sent for invoice \${inv.invoiceNumber}\`);
}

app.listen(3000, () => console.log('Webhook listener running on port 3000'));`;


/* ============================================================
   DOM helpers
   ============================================================ */

function $(id) { return document.getElementById(id); }

/* ============================================================
   Credential management
   ============================================================ */

function updateCredsUI() {
  const credsSaved = creds.googleClientId.length > 0 && creds.xeroSecret.length > 0;
  const fullyReady = credsSaved && googleAccessToken !== null && Date.now() < tokenExpiresAt;

  // Status dot + label
  $('credsDot').classList.toggle('configured', fullyReady);
  $('credsLabel').textContent = fullyReady
    ? 'Configured'
    : credsSaved ? 'Credentials saved — connect Gmail' : 'Not configured';

  // Enable/disable Connect Gmail button
  $('connectGoogleBtn').disabled = !credsSaved;

  // Show/hide auth bar
  const bar = $('googleAuthBar');
  if (fullyReady) {
    bar.classList.remove('hidden');
  } else {
    bar.classList.add('hidden');
  }

  // Enable/disable Send Test button
  $('sendBtn').disabled = !fullyReady;
  $('sendBtn').title    = fullyReady ? '' : 'Connect Gmail first';

  // Filled-input styling
  ['googleClientId', 'xeroSecret'].forEach(function(key) {
    $(key).classList.toggle('filled', creds[key].length > 0);
  });
}

$('saveCredsBtn').addEventListener('click', function() {
  const clientId  = $('googleClientId').value.trim();
  const xeroSec   = $('xeroSecret').value.trim();

  if (!clientId || !xeroSec) {
    flashPanel('credsPanel', 'error');
    return;
  }

  creds.googleClientId = clientId;
  creds.xeroSecret     = xeroSec;

  updateCredsUI();
  flashPanel('credsPanel', 'success');
});

$('clearCredsBtn').addEventListener('click', function() {
  creds.googleClientId = '';
  creds.xeroSecret     = '';
  $('googleClientId').value = '';
  $('xeroSecret').value     = '';
  googleAccessToken = null;
  tokenExpiresAt    = 0;
  updateCredsUI();
});

$('revokeGoogleBtn').addEventListener('click', function() {
  if (googleAccessToken) {
    // Best-effort token revocation
    fetch('https://oauth2.googleapis.com/revoke?token=' + googleAccessToken, { method: 'POST' })
      .catch(function() {});
  }
  googleAccessToken = null;
  tokenExpiresAt    = 0;
  updateCredsUI();
});

/* Flash panel border for feedback */
function flashPanel(panelId, type) {
  const panel = $(panelId);
  const color = type === 'success' ? 'rgba(200,245,66,0.4)' : 'rgba(255,80,80,0.4)';
  panel.style.transition = 'box-shadow 0.1s';
  panel.style.boxShadow  = '0 0 0 1px ' + color;
  setTimeout(function() { panel.style.boxShadow = 'none'; }, 700);
}

/* Show/hide password toggles */
document.querySelectorAll('.cred-toggle').forEach(function(btn) {
  btn.addEventListener('click', function() {
    var input = $(btn.dataset.target);
    input.type = input.type === 'password' ? 'text' : 'password';
  });
});

/* ============================================================
   Google OAuth 2.0 — implicit (token) flow via GIS
   ============================================================ */

$('connectGoogleBtn').addEventListener('click', function() {
  if (!creds.googleClientId) return;

  // Google Identity Services tokenClient (implicit grant)
  const tokenClient = google.accounts.oauth2.initTokenClient({
    client_id: creds.googleClientId,
    scope: GMAIL_SCOPE,
    callback: function(tokenResponse) {
      if (tokenResponse.error) {
        showResult('failure', '\u2717 Google auth error: ' + tokenResponse.error);
        return;
      }
      googleAccessToken = tokenResponse.access_token;
      // expires_in is in seconds; subtract 60s buffer
      tokenExpiresAt = Date.now() + (tokenResponse.expires_in - 60) * 1000;
      updateCredsUI();
    }
  });

  tokenClient.requestAccessToken({ prompt: 'consent' });
});

/* ============================================================
   Gmail API — send email via REST
   ============================================================ */

/**
 * Build a base64url-encoded RFC 2822 message and POST it to
 * the Gmail users.messages.send endpoint.
 */
async function sendGmailEmail(to, subject, bodyText) {
  if (!googleAccessToken || Date.now() >= tokenExpiresAt) {
    throw new Error('Gmail not authorised. Please reconnect via the Connect Gmail button.');
  }

  // Compose RFC 2822 message
  const message =
    'To: ' + to + '\r\n' +
    'Subject: ' + subject + '\r\n' +
    'Content-Type: text/plain; charset=utf-8\r\n' +
    '\r\n' +
    bodyText;

  // base64url encode (no padding '+' → '-', '/' → '_', strip '=')
  const encoded = btoa(unescape(encodeURIComponent(message)))
    .replace(/\+/g, '-')
    .replace(/\//g, '_')
    .replace(/=+$/, '');

  const response = await fetch(
    'https://gmail.googleapis.com/gmail/v1/users/me/messages/send',
    {
      method: 'POST',
      headers: {
        'Authorization': 'Bearer ' + googleAccessToken,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ raw: encoded })
    }
  );

  if (!response.ok) {
    const errData = await response.json().catch(function() { return {}; });
    const msg = (errData.error && errData.error.message) ? errData.error.message : ('HTTP ' + response.status);
    throw new Error('Gmail API: ' + msg);
  }

  return await response.json(); // { id, threadId, labelIds }
}

/* ============================================================
   Test notification handler
   ============================================================ */

$('sendBtn').addEventListener('click', async function() {
  var btn = $('sendBtn');
  btn.disabled    = true;
  btn.textContent = 'Sending\u2026';
  $('testResult').className = 'test-result hidden';

  const subject = '[Xero] Bill Submitted for Approval \u2013 TEST-INV-2024-0001';
  const body    =
    'Hello David,\n\n' +
    'A new bill has been submitted for approval in Xero.\n\n' +
    'Bill Details:\n' +
    '\u2022 Vendor: Test Vendor Inc.\n' +
    '\u2022 Invoice Number: TEST-INV-2024-0001\n' +
    '\u2022 Amount: $1,000.00\n' +
    '\u2022 Submitted: ' + new Date().toLocaleString() + '\n' +
    '\u2022 Status: Awaiting Approval\n\n' +
    'Please log in to Xero to review and approve this bill.\n\n' +
    'This is an automated notification from the Xero Bill Approval Notifier.';

  try {
    const result = await sendGmailEmail(RECIPIENT, subject, body);

    events.unshift({
      id:         Date.now(),
      vendor:     'Test Vendor Inc.',
      amount:     '$1,000.00',
      invoiceNum: 'TEST-INV-2024-0001',
      status:     'sent',
      time:       'just now'
    });
    renderLog();
    updateStats();

    showResult('success', '\u2713 Email sent via Gmail API. Message ID: ' + result.id);

  } catch (err) {
    events.unshift({
      id:         Date.now(),
      vendor:     'Test Vendor Inc.',
      amount:     '$1,000.00',
      invoiceNum: 'TEST-INV-2024-0001',
      status:     'failed',
      time:       'just now'
    });
    renderLog();
    updateStats();

    showResult('failure', '\u2717 ' + err.message);
  }

  btn.disabled    = false;
  btn.textContent = 'Send Test \u2192';
});

function showResult(type, text) {
  var el = $('testResult');
  el.className   = 'test-result ' + type;
  el.textContent = text;
}

/* ============================================================
   Tab switching
   ============================================================ */

function activateTab(name) {
  document.querySelectorAll('.tab').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.tab === name);
  });
  document.querySelectorAll('.tab-panel').forEach(function(panel) {
    var isTarget = panel.id === 'panel-' + name;
    panel.classList.toggle('hidden', !isTarget);
    if (isTarget) {
      panel.classList.remove('fade-in');
      void panel.offsetWidth;
      panel.classList.add('fade-in');
    }
  });
}

document.querySelectorAll('.tab').forEach(function(btn) {
  btn.addEventListener('click', function() { activateTab(btn.dataset.tab); });
});

/* ============================================================
   Status dot pulse
   ============================================================ */

(function startPulse() {
  var dot = $('statusDot');
  setInterval(function() { dot.classList.toggle('pulse'); }, 1500);
})();

/* ============================================================
   Render event log
   ============================================================ */

function renderLog() {
  var log = $('eventLog');
  log.innerHTML = '';
  events.forEach(function(e) {
    var item = document.createElement('div');
    item.className = 'log-item';
    item.innerHTML =
      '<div class="log-icon">' +
        '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">' +
          '<path d="M1 3l6 4 6-4M1 3v8h12V3" stroke="#c8f542" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"/>' +
        '</svg>' +
      '</div>' +
      '<div class="log-info">' +
        '<div class="log-vendor">' + e.vendor + ' <span class="sep">\u00b7</span> <span class="inv">' + e.invoiceNum + '</span></div>' +
        '<div class="log-dest">' + e.amount + ' \u2192 ' + RECIPIENT + '</div>' +
      '</div>' +
      '<div class="log-meta">' +
        '<span class="badge badge-' + e.status + '">' + e.status + '</span>' +
        '<div class="log-time">' + e.time + '</div>' +
      '</div>';
    log.appendChild(item);
  });
}

function updateStats() {
  $('statCount').textContent = events.filter(function(e) { return e.status === 'sent'; }).length;
}

/* ============================================================
   Populate code block
   ============================================================ */

(function populateCode() {
  var pre  = $('codeBlock');
  var safe = CODE_SNIPPET
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  pre.innerHTML = safe;
})();

/* ============================================================
   Initial render
   ============================================================ */

renderLog();
updateStats();
updateCredsUI();
