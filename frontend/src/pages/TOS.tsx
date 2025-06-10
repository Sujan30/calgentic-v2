import React from 'react';
import { Link } from 'react-router-dom';
import Header from '@/components/Header';
import Footer from '@/components/Footer';

const TosPage = () => {
  return (
    <div className="min-h-screen w-full bg-white dark:bg-black text-gray-900 dark:text-gray-100">
      <Header />

      <section className="pt-32 section-padding pb-20">
        <div className="max-w-3xl mx-auto animate-fade-up">
          <h1 className="text-4xl sm:text-5xl font-bold mb-4">Terms of Service</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-12">
            Last Updated: June 1, 2025
          </p>

          {/* 1. Introduction */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">1. Introduction</h2>
            <p className="text-base text-gray-600 dark:text-gray-300">
              Calgentic (“we,” “us,” or “our”) is a personal project—an experimental web/app interface created by Sujan Nandikol Sunilkumar. This Privacy Policy describes what information Calgentic collects, how it’s used, and the choices you have regarding your data. By using Calgentic, you agree to the terms below.
            </p>
          </div>

          {/* 2. Information We Collect */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">2. Information We Collect</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-4">
              Depending on how you’ve set up Calgentic, you may collect some or all of the following:
            </p>
            <ul className="list-decimal list-inside space-y-3 text-base text-gray-600 dark:text-gray-300">
              <li>
                <span className="font-medium">Account &amp; Profile Data (if you require sign-up):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Email address (for login, password resets, notifications)</li>
                  <li>Username or display name</li>
                  <li>Password (securely hashed; you should never store plaintext)</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Usage &amp; Technical Data (automatically collected):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>IP address and approximate location (city/region)</li>
                  <li>Browser type and version (e.g., Chrome 120, Safari 17)</li>
                  <li>Device and operating system (e.g., Windows 10, macOS 14)</li>
                  <li>Timestamps of page views, actions, and API calls</li>
                  <li>Referring URL and pages you visit in the app</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Cookies &amp; Local Storage:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Session cookies (to keep you logged in during a session)</li>
                  <li>“Remember me” tokens (if you opted to stay logged in)</li>
                  <li>Any analytics cookies (e.g., Google Analytics) if you’ve installed an analytics snippet</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">User-Generated Content (if applicable):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Profile picture uploads or file attachments</li>
                  <li>In-app messages, comments, or form inputs</li>
                </ul>
              </li>
            </ul>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              <strong>Note:</strong> If Calgentic does not require sign-up or file uploads, simply omit Sections 2.1 and 2.4.
            </p>
          </div>

          {/* 3. How We Use Your Information */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">3. How We Use Your Information</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-4">
              We only use collected data to provide, maintain, and improve Calgentic. Specific uses may include:
            </p>
            <ul className="list-disc list-inside space-y-3 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>
                <span className="font-medium">Authentication &amp; Security:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Verifying your identity when you log in</li>
                  <li>Resetting your password</li>
                  <li>Protecting against unauthorized access</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Service Operation &amp; Improvement:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Displaying personalized content or settings</li>
                  <li>Debugging errors and monitoring performance</li>
                  <li>Tracking feature usage to optimize functionality</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Communication (if you opted in):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Sending transactional emails (e.g., “reset your password” emails)</li>
                  <li>Optional: Newsletters or project updates (only if you explicitly signed up)</li>
                </ul>
              </li>
            </ul>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              If you don’t collect marketing emails, simply remove any reference to newsletters/updates.
            </p>
          </div>

          {/* 4. Cookies & Tracking Technologies */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">4. Cookies &amp; Tracking Technologies</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-4">
              Calgentic may use cookies or similar technologies to enhance your experience:
            </p>
            <ul className="list-decimal list-inside space-y-3 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>
                <span className="font-medium">Strictly Necessary Cookies:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Keep you logged in during a session</li>
                  <li>Prevent CSRF or other security issues</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Functional Cookies (optional):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>“Remember me” tokens across sessions</li>
                  <li>Theme or language preferences</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Analytics Cookies (optional):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Google Analytics (or another analytics provider) to understand usage patterns</li>
                  <li>We do not use cookies for targeted advertising or third-party ad networks</li>
                </ul>
              </li>
            </ul>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              When you first visit Calgentic, you may see a banner asking for cookie consent. You can generally disable cookies in your browser settings, but some features (like staying logged in) may not work correctly without them.
            </p>
          </div>

          {/* 5. Data Sharing & Disclosure */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">5. Data Sharing &amp; Disclosure</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-4">
              Because Calgentic is a personal project:
            </p>
            <ul className="list-disc list-inside space-y-3 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>We do not sell, rent, or share your personal data with advertisers.</li>
              <li>
                We may share data with third-party services that help us run the project, such as:
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>Hosting/Servers: e.g., Render</li>
                  <li>Database Provider: e.g., Supabase</li>
                  <li>Email Service: e.g., SendGrid, Mailchimp</li>
                  <li>Analytics: e.g., Google Analytics</li>
                </ul>
              </li>
            </ul>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              All of these subprocessors are contractually obligated to keep your data safe and only use it for the purposes we specify (e.g., storing user credentials, sending transactional emails, collecting anonymized usage data).
            </p>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              <span className="font-medium">Legal Requests:</span> In the rare event we receive a valid subpoena or court order, we may be compelled to share certain information with law enforcement authorities. We would notify you first unless prohibited by law.
            </p>
          </div>

          {/* 6. Data Retention */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">6. Data Retention</h2>
            <ul className="list-disc list-inside space-y-3 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>
                <span className="font-medium">Account Data:</span> We keep your account data (email, username, hashed password) as long as your account is active. If you request deletion, we’ll remove all personal identifiers within 30 days.
              </li>
              <li>
                <span className="font-medium">Logs &amp; Analytics:</span> Usage logs and analytics data are stored for up to 12 months, then automatically purged. We retain anonymized/aggregated data indefinitely to understand long-term usage trends.
              </li>
              <li>
                <span className="font-medium">User-Generated Content:</span> If you uploaded any file or posted content, it will remain unless you delete your account or request content removal. Deletion requests for user uploads will be processed within 14 days.
              </li>
            </ul>
          </div>

          {/* 7. Your Rights & Choices */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">7. Your Rights &amp; Choices</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-4">
              Even though Calgentic is a small project, we want you to know your options:
            </p>
            <ol className="list-decimal list-inside space-y-3 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>
                <span className="font-medium">Access &amp; Correction:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>You can view or update your profile data (email, username) by logging into your account and editing your settings.</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Account Deletion (“Right to be Forgotten”):</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>
                    To delete your account and all associated data, email us at{' '}
                    <a href="mailto:nandikolsujan@gmail.com" className="text-primary hover:underline">
                      nandikolsujan@gmail.com
                    </a>
                    . We’ll remove your personal information within 30 days.
                  </li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Opting Out of Marketing Emails:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>If you signed up for occasional updates, every email will include an “Unsubscribe” link. You can also email us directly to opt out at any time.</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Cookies:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>You can disable or clear cookies through your browser settings. Disabling essential cookies may prevent certain features (like staying logged in) from working properly.</li>
                </ul>
              </li>
              <li>
                <span className="font-medium">Data Portability:</span>
                <ul className="list-disc list-inside pl-5 mt-2 space-y-1">
                  <li>
                    If you’d like a copy of your data (e.g., profile info, any uploaded content), request it via{' '}
                    <a href="mailto:nandikolsujan@gmail.com" className="text-primary hover:underline">
                      nandikolsujan@gmail.com
                    </a>
                    . We’ll send it in a machine-readable JSON format within 14 days.
                  </li>
                </ul>
              </li>
            </ol>
          </div>

          {/* 8. Security Measures */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">8. Security Measures</h2>
            <ul className="list-disc list-inside space-y-3 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>
                <span className="font-medium">Encryption in Transit:</span> All data transmitted between you and Calgentic is over HTTPS/TLS.
              </li>
              <li>
                <span className="font-medium">Password Storage:</span> User passwords are hashed with a secure algorithm (e.g., bcrypt or Argon2) before being stored—never in plaintext.
              </li>
              <li>
                <span className="font-medium">Access Controls:</span> Only the project owner (you) and any authorized collaborators can access production servers and databases. You’re encouraged to use two-factor authentication (2FA) for your hosting/service provider accounts.
              </li>
              <li>
                <span className="font-medium">Regular Updates &amp; Patching:</span> Dependencies and libraries are kept up-to-date to minimize vulnerabilities.
              </li>
            </ul>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              Despite these measures, no system is 100% secure. If there’s ever a data breach, we’ll notify affected users at{' '}
              <a href="mailto:nandikolsujan@gmail.com" className="text-primary hover:underline">
                nandikolsujan@gmail.com
              </a>{' '}
              within 72 hours of discovery.
            </p>
          </div>

          {/* 9. Children’s Privacy */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">9. Children’s Privacy</h2>
            <p className="text-base text-gray-600 dark:text-gray-300">
              Calgentic is not intended for users under 13 years old. We do not knowingly collect personal information from children under 13. If you’re a parent or guardian and believe we’ve unintentionally gathered data from a child under 13, please contact us at{' '}
              <a href="mailto:nandikolsujan@gmail.com" className="text-primary hover:underline">
                nandikolsujan@gmail.com
              </a>
              , and we will delete that information promptly.
            </p>
          </div>

          {/* 9. Children’s Privacy */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">10. Use of Google User Data for AI/ML Purposes</h2>
            <p className="text-base text-gray-600 dark:text-gray-300">
              We do not use any Google user data—whether directly or indirectly—for the development, improvement, or training of artificial intelligence (AI) or machine learning (ML) models. This includes any form of training data, fine-tuning, or algorithmic optimization. All Google user data accessed by our app is used solely for providing and improving core user-facing features, and is handled in accordance with Google’s Limited Use requirements.
            </p>
            <p className='text-base text-gray-600 dark:text-gray-300'>
              We do not use any data obtained through Google Workspace APIs to develop, improve, or train non-personalized artificial intelligence (AI) or machine learning (ML) models. All data accessed via these APIs is strictly used to provide user-requested functionality within the app and in full compliance with Google’s Limited Use Policy.
              If our application transfers Google user data obtained from Workspace APIs to third-party AI tools, we do so only for user-initiated, personalized functionality. We do not transfer any Google user data for the purpose of training, developing, or improving generalized or non-personalized AI or ML models. The data transferred is limited to what is strictly necessary to perform the specific task requested by the user.

            </p>
          </div>
          {/* 10. International Data Transfers */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">11. International Data Transfers</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-2">
              If you’re visiting Calgentic from outside the United States, please note your data may be transferred to and stored on servers located in the U.S. By using Calgentic, you consent to this transfer.
            </p>
            <p className="text-base text-gray-600 dark:text-gray-300">
              If you’re an EU resident, you have certain rights under the GDPR (e.g., access, correction, erasure). To exercise any of these rights, email{' '}
              <a href="mailto:nandikolsujan@gmail.com" className="text-primary hover:underline">
                nandikolsujan@gmail.com
              </a>
              .
            </p>
          </div>

          {/* 11. Third-Party Links & Embedded Content */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">12. Third-Party Links &amp; Embedded Content</h2>
            <p className="text-base text-gray-600 dark:text-gray-300">
              Calgentic may include links or embed content from third parties (e.g., YouTube videos, social media widgets). We are not responsible for how those third parties collect or use your data. Please review their separate privacy policies before interacting with their content.
            </p>
          </div>

          {/* 12. Changes to This Privacy Policy */}
          <div className="mb-8">
            <h2 className="text-2xl font-semibold mb-3">13. Changes to This Privacy Policy</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-2">
              We may update this policy from time to time. If we make material changes affecting your rights or the way we use personal data, we’ll:
            </p>
            <ol className="list-decimal list-inside space-y-2 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>Post the updated Privacy Policy here with a new “Last Updated” date.</li>
              <li>If you have an account, we’ll send a notice to your registered email address.</li>
            </ol>
            <p className="mt-4 text-base text-gray-600 dark:text-gray-300">
              Your continued use of Calgentic after such changes means you accept the updated policy.
            </p>
          </div>

          {/* 13. Contact Us */}
          <div className="mb-12">
            <h2 className="text-2xl font-semibold mb-3">14. Contact Us</h2>
            <p className="text-base text-gray-600 dark:text-gray-300 mb-2">
              If you have any questions, concerns, or requests regarding this Privacy Policy—or if you want to delete your data—please reach out to:
            </p>
            <ul className="list-disc list-inside space-y-2 text-base text-gray-600 dark:text-gray-300 pl-5">
              <li>
                <span className="font-medium">Email:</span>{' '}
                <a href="mailto:nandikolsujan@gmail.com" className="text-primary hover:underline">
                  nandikolsujan@gmail.com
                </a>
              </li>
              <li>
                <span className="font-medium">Project Owner:</span> Sujan Nandikol Sunilkumar
              </li>
            </ul>
          </div>

          {/* Footer Links */}
          
        </div>
      </section>
    <Footer/>
    </div>
  );
};

export default TosPage;
