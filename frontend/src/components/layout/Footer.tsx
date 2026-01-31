import { Activity, Github, Mail, Phone } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-900 text-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center space-x-2 mb-4">
              <Activity className="h-8 w-8 text-healthcare-accent" />
              <span className="text-xl font-bold">SmartCare</span>
            </div>
            <p className="text-gray-400 max-w-md">
              AI-powered patient queue and triage optimization system. 
              Reducing wait times, improving healthcare delivery.
            </p>
          </div>

          {/* Quick Links */}
          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-gray-400">
              <li><a href="/checkin" className="hover:text-white transition-colors">Patient Check-In</a></li>
              <li><a href="/queue" className="hover:text-white transition-colors">Queue Status</a></li>
              <li><a href="/doctor" className="hover:text-white transition-colors">Doctor Portal</a></li>
              <li><a href="/admin" className="hover:text-white transition-colors">Admin Dashboard</a></li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <ul className="space-y-2 text-gray-400">
              <li className="flex items-center space-x-2">
                <Mail className="h-4 w-4" />
                <span>support@smartcare.health</span>
              </li>
              <li className="flex items-center space-x-2">
                <Phone className="h-4 w-4" />
                <span>+91 123-456-7890</span>
              </li>
              <li className="flex items-center space-x-2">
                <Github className="h-4 w-4" />
                <a href="https://github.com/KomalLaddha-dev/HackNagpur" className="hover:text-white">
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-center text-gray-400">
          <p>&copy; 2026 SmartCare. Built with ❤️ for HackNagpur</p>
        </div>
      </div>
    </footer>
  )
}
