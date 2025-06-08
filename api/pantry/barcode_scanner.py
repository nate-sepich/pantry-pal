import cv2
from pyzbar.pyzbar import decode, ZBarSymbol
import numpy as np
import requests
from dotenv import load_dotenv
import os
# Load environment variables from .env file
load_dotenv()
USDA_API_KEY = os.getenv('USDA_API_KEY')
def decode_barcodes(image):
    # Decode barcodes in the image (no restrictions on barcode type)
    barcodes = decode(image)

    barcode_info = []

    for barcode in barcodes:
        data = barcode.data.decode('utf-8')
        barcode_type = barcode.type
        barcode_info.append((data, barcode_type))

        # Draw bounding box around the barcode
        points = barcode.polygon
        if len(points) > 4:  # Adjust for irregular quadrilaterals
            hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
            points = hull.astype(int).tolist()

        # Only proceed if points are valid
        if len(points) >= 4:
            for i in range(len(points)):
                pt1 = tuple(points[i])
                pt2 = tuple(points[(i + 1) % len(points)])
                
                # Ensure the points are tuples of length 2
                if len(pt1) == 2 and len(pt2) == 2:
                    cv2.line(image, pt1, pt2, (0, 255, 0), 3)

        # Display the barcode data and type on the image
        if barcode.rect:
            cv2.putText(image, f"{data} ({barcode_type})", (barcode.rect.left, barcode.rect.top - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
    
    return image, barcode_info

# Initialize webcam
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Error: Could not open webcam.")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame.")
            break

        # Process and decode barcodes
        img_with_barcodes, barcode_info = decode_barcodes(frame)

        # Show the frame with bounding boxes and text
        cv2.imshow("Barcode Scanner", img_with_barcodes)

        # Display barcode information and make API requests
        if barcode_info:
            for data, barcode_type in barcode_info:
                print(f"Detected barcode: {data} ({barcode_type})")
                search_url = f"https://api.nal.usda.gov/fdc/v1/foods/search?api_key={USDA_API_KEY}"
                params = {'query': data}
                response = requests.get(search_url, params=params)
                if response.status_code == 200:
                    data = response.json()
                    food_item = data['foods'][0]
                    print("Food Item Found:")
                    print(f"Name: {food_item['description']}")
                    print(f"FDC ID: {food_item['fdcId']}")
                    print(f"Brand Name: {food_item.get('brandOwner', 'N/A')}")
                    print(f"Category: {food_item.get('foodCategory', 'N/A')}")
                else:
                    print(f"Error: {response.status_code}, Could not retrieve data.")
        
        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the webcam and close windows
    cap.release()
    cv2.destroyAllWindows()