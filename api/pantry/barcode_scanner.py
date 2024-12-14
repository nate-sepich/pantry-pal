import cv2
import numpy as np
from pyzbar.pyzbar import decode, ZBarSymbol
import datetime

# Function to save barcode data to a file
def save_to_file(data, barcode_type):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open("scanned_barcodes.txt", "a") as file:
        file.write(f"{timestamp} - Type: {barcode_type}, Data: {data}\n")
    print(f"Saved: {data} ({barcode_type})")

# Initialize the camera
def initialize_camera():
    for i in range(5):  # Try different device indexes
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Camera initialized on device {i}")
            return cap
    raise Exception("No camera detected!")

def main():
    try:
        cap = initialize_camera()
        print("Press 's' to save a barcode manually, 'q' to quit.")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture frame. Exiting...")
                break
            
            # Decode barcodes in the frame
            try:
                barcodes = decode(frame, symbols=[ZBarSymbol.CODE128, ZBarSymbol.QRCODE])
            except Exception as e:
                print(f"Decoding error: {e}")
                continue

            for barcode in barcodes:
                data = barcode.data.decode('utf-8')
                barcode_type = barcode.type
                print(f"Detected: {data} ({barcode_type})")

                # Draw bounding box around the barcode
                points = barcode.polygon
                if len(points) > 4:  # Adjust for irregular quadrilaterals
                    hull = cv2.convexHull(
                        np.array([point for point in points], dtype=np.float32)
                    )
                    points = hull.astype(int).tolist()
                if points:
                    for i in range(len(points)):
                        cv2.line(
                            frame,
                            tuple(points[i]),
                            tuple(points[(i + 1) % len(points)]),
                            (0, 255, 0),
                            3,
                        )
                
                # Display the barcode data and type on the frame
                cv2.putText(
                    frame,
                    f"{data} ({barcode_type})",
                    (barcode.rect.left, barcode.rect.top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 0),
                    2,
                )
            
            # Show the frame
            cv2.imshow("Barcode Scanner", frame)

            # Wait for key press
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):  # Quit
                break
            elif key == ord('s'):  # Save barcodes
                if barcodes:
                    for barcode in barcodes:
                        data = barcode.data.decode('utf-8')
                        barcode_type = barcode.type
                        save_to_file(data, barcode_type)
                else:
                    print("No barcode detected to save.")

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
