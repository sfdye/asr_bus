import Cocoa
import CoreLocation

class AppDelegate: NSObject, NSApplicationDelegate, CLLocationManagerDelegate {
    let manager = CLLocationManager()
    var didFinish = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyHundredMeters

        switch manager.authorizationStatus {
        case .notDetermined:
            manager.requestAlwaysAuthorization()
        case .denied, .restricted:
            fputs("error:denied — grant permission in System Settings > Privacy & Security > Location Services\n", stderr)
            quit(1)
        case .authorizedAlways, .authorized:
            manager.requestLocation()
        default:
            manager.requestAlwaysAuthorization()
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 10) { [weak self] in
            guard let self = self, !self.didFinish else { return }
            fputs("error:timeout\n", stderr)
            self.quit(1)
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        switch manager.authorizationStatus {
        case .denied, .restricted:
            fputs("error:denied\n", stderr)
            quit(1)
        case .authorizedAlways, .authorized:
            manager.requestLocation()
        default:
            break
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let loc = locations.last else { return }
        let output = "\(loc.coordinate.latitude),\(loc.coordinate.longitude)"
        try? output.write(toFile: "/tmp/asr_bus_location.txt", atomically: true, encoding: .utf8)
        quit(0)
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        fputs("error:\(error.localizedDescription)\n", stderr)
        quit(1)
    }

    func quit(_ code: Int32) -> Never {
        didFinish = true
        exit(code)
    }
}

let app = NSApplication.shared
app.setActivationPolicy(.accessory)
let delegate = AppDelegate()
app.delegate = delegate
app.run()
