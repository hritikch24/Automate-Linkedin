const { google } = require('googleapis');
const http = require('http');
const url = require('url');
const fs = require('fs');
const open = require('open');
const destroyer = require('server-destroy');

// Replace with your credentials from GitHub secrets
const CLIENT_ID = process.env.YOUTUBE_CLIENT_ID || 'YOUR_CLIENT_ID';
const CLIENT_SECRET = process.env.YOUTUBE_CLIENT_SECRET || 'YOUR_CLIENT_SECRET';
const REDIRECT_URI = 'http://localhost:8080/oauth2callback';

const SCOPES = [
  'https://www.googleapis.com/auth/youtube.upload',
  'https://www.googleapis.com/auth/youtube'
];

async function getNewToken() {
  return new Promise((resolve, reject) => {
    try {
      const oauth2Client = new google.auth.OAuth2(
        CLIENT_ID, 
        CLIENT_SECRET, 
        REDIRECT_URI
      );

      const authUrl = oauth2Client.generateAuthUrl({
        access_type: 'offline',
        scope: SCOPES,
        prompt: 'consent',
        include_granted_scopes: true
      });

      const server = http.createServer(async (req, res) => {
        try {
          if (req.url.indexOf('/oauth2callback') > -1) {
            const qs = new url.URL(req.url, 'http://localhost:8080').searchParams;
            const code = qs.get('code');
            
            if (!code) {
              throw new Error('No code received from Google');
            }
            
            console.log('Code received');
            
            const { tokens } = await oauth2Client.getToken(code);
            console.log('Token exchange successful!');
            
            if (!tokens.refresh_token) {
              throw new Error('No refresh token returned. Please revoke access and try again.');
            }
            
            // Save tokens to file
            fs.writeFileSync('youtube_tokens.json', JSON.stringify(tokens, null, 2));
            
            res.writeHead(200, {'Content-Type': 'text/html'});
            res.end(`
              <h1>Authentication Successful!</h1>
              <p>Your new refresh token has been saved to youtube_tokens.json</p>
              <p>Refresh Token: <code>${tokens.refresh_token}</code></p>
              <p>You can close this window now.</p>
            `);
            
            resolve(tokens);
            server.destroy();
          }
        } catch (error) {
          console.error('Error handling callback:', error);
          res.writeHead(500, {'Content-Type': 'text/html'});
          res.end(`<h1>Error</h1><p>${error.message}</p>`);
          reject(error);
          server.destroy();
        }
      });
      
      server.listen(8080, () => {
        console.log('Authorization server is running at http://localhost:8080');
        console.log('\nOpening browser for authorization...');
        console.log('If the browser doesn\'t open automatically, use this URL:');
        console.log('\n', authUrl, '\n');
        
        open(authUrl, {wait: false}).catch(() => {
          console.log('Failed to open browser automatically. Please open the URL manually.');
        });
      });
      
      destroyer(server);
      
    } catch (error) {
      console.error('Error in authentication process:', error);
      reject(error);
    }
  });
}

async function main() {
  try {
    console.log('Starting YouTube OAuth process...');
    const tokens = await getNewToken();
    
    console.log('\n=== AUTHENTICATION SUCCESSFUL ===');
    console.log('Refresh Token:', tokens.refresh_token);
    console.log('Token Expiry:', new Date(tokens.expiry_date).toISOString());
    console.log('=================================\n');
    
    console.log('\nAdd this refresh token to your GitHub secrets as YOUTUBE_REFRESH_TOKEN:');
    console.log(tokens.refresh_token);
  } catch (error) {
    console.error('Authentication process failed:', error);
  }
}

main();