![image](https://github.com/user-attachments/assets/0552cef2-b050-4c63-8cdf-913cb60c8fc3)

# 🌟 LesionLens: Automated Detection of Intra-Bony Jaw Lesions

Welcome to **LesionLens**, an end-to-end AI pipeline that transforms panoramic dental X‑rays into actionable clinical insights—lightning-fast lesion detection powered by YOLOv11, seamless dataset management via Roboflow, and an intelligent AI agent for instant report generation.

---

## 🎯 Research Objectives
1. **Automate** localization and classification of intra-bony jaw lesions in panoramic radiographs.  
2. **Benchmark** YOLOv11 performance against expert radiologist annotations.  
3. **Streamline** clinical reporting via a generative AI agent.  
4. **Deploy** a lightweight inference service for real‑world dental workflows.

---

## 📂 Dataset
- **Source:** 3,315 panoramic radiographs curated from institutional archives.  
- **Annotations:** Expert-delineated bounding boxes for periapical and other intra‑bony lesions.  
- **Splits:** 70% train, 15% validation, 15% test.

---

## 🛠️ Roboflow Integration
We leverage Roboflow to:  
- Import raw images and metadata.  
- Standardize annotations (COCO/TXT).  
- Perform on‑the‑fly augmentations: random rotation, scaling, brightness shifts.  
- Export ready‑to‑train datasets at 640×640 px.

---

## 🖥️ System Design & Web Interface

Visualize how LesionLens ties together a responsive front-end, backend inference service, and data storage:
Login Page
Users must authenticate using their email and password to access the system. This secure login form helps manage role-based access for administrators and medical professionals.

![image](https://github.com/user-attachments/assets/4a3fe154-c78c-4b5e-951a-2b50fe6f8dc2)

Add User Page
Administrators can add new users by filling out details such as name, email, phone number, gender, and password. This facilitates secure access control and multi-user support.

![image](https://github.com/user-attachments/assets/756e2987-f7f4-4e65-b5b6-70c47dd7cc23)

Add Patient Page
Patient records can be added by authorized users, including demographic and medical details such as age, height, weight, and description of symptoms. This enables personalized diagnostic tracking.

![image](https://github.com/user-attachments/assets/f86d5a2f-e968-4262-9320-63c493c98042)

Diagnosis Page 
The user selects an X-ray image for diagnosis. Fields for the patient’s name and email are entered to associate the result with their profile.

![image](https://github.com/user-attachments/assets/35f4c64c-6a6a-40e1-a2ae-109c4776dbc6)

Diagnosis History Page
displays previously processed patient cases, showing diagnosis results, dates, and user actions. It helps track patient progress and outcomes.

![image](https://github.com/user-attachments/assets/0fcad922-6f5f-4b8c-8435-a4494a843900)

Manage Users Page
Admins can manage existing users by viewing their contact details and deleting users when needed. This interface supports platform maintenance and security.

![image](https://github.com/user-attachments/assets/02ec0713-c238-4362-9843-1eebebece48b)

Edit Profile Page
Users can edit their contact information and update demographic details such as gender, city, and age. This keeps user records up-to-date.

![image](https://github.com/user-attachments/assets/8276d93b-636e-4aae-a2c3-98df4b90b919)


---



## 🔍 Model Selection

![image](https://github.com/user-attachments/assets/377369b9-629a-4c5b-b102-bb8e2a3e95c5)

- **Base:** YOLOv11 (C3K2, SPPF, C2PSA modules)  
- **Backbone:** CSPDarknet with optimized depth and width scaling.  
- **Head:** Anchor‑based detection with multi‑scale feature fusion.

---

## 📊 Performance Metrics
- **mAP@0.5:** Mean Average Precision at IoU 0.5.
- **mAP@0.5:0.95:** COCO-style averaged across IoU thresholds.

![image](https://github.com/user-attachments/assets/b6282b0c-7ed2-4af7-96e1-4207c75911c6)

- **Precision & Recall:** Lesion-specific classification performance.

![image](https://github.com/user-attachments/assets/b6282b0c-7ed2-4af7-96e1-4207c75911c6)
![image](https://github.com/user-attachments/assets/2c62e70c-56b2-4aae-8df6-617ffede54b1)


---

🚀 Methodology

Preprocessing

- Grayscale conversion, histogram equalization.

- Resize to 640×640 px, normalize.

Augmentation

- Geometric: random rotation (±15°), horizontal/vertical flips, scaling (±10%), translation (±10%).
- Photometric: brightness adjustment (±20%), contrast jitter, Gaussian blur, Gaussian noise.

![image](https://github.com/user-attachments/assets/e1b69671-8ccf-4f41-b3ed-10786d279d5c)

![image](https://github.com/user-attachments/assets/744ae392-d974-4bc1-ab3f-f887febe2257)
Training

- Optimizer: SGD (LR=0.01, momentum=0.9).

- Epochs: 150 with early stopping.

- Batch size: 16, mixed precision.

Validation

- Monitor mAP metrics, checkpoint best weights.

Testing & Inference

- Generate JSON detection outputs + annotated PNGs.

---

## 📈 Results
| Metric           | Results    |
|------------------|------------|
| mAP@0.5          | 66.8%      | 
| mAP@0.5:0.95     | 41.3%      | 
| Precision        | 75.8%      | 
| Recall           | 67.1%      | 


---

## 🤖 AI Agent for Automated Reporting
A custom generative AI agent consumes detection outputs to draft clinical reports:
- **Lesion Summary:** Locations, sizes, confidence scores.  
- **Diagnostic Insights:** Contextual interpretation based on lesion type.  
- **Recommendations:** Follow-up imaging, biopsy suggestions.  
- **Editable Draft:** Clinician can refine before sign‑off.

---

## 🩻 X-ray Input & Detection Workflow

Input Upload: Clinician drops a PAN image into the interface.
example:![3](https://github.com/user-attachments/assets/a1ae3974-8dbd-4bb1-b6f2-05d5d03beea2)


Detection Overlay: YOLOv11 bounding boxes rendered on the image with confidence scores.
example: ![image](https://github.com/user-attachments/assets/1c23bbac-9c8a-4f0f-8539-1d44bbfa75b5)

---

## 🗣️ Discussion & Limitations
- **Strengths:** High precision, rapid inference, seamless report automation.  
- **Limitations:**  
  - Challenged by extremely small/low-contrast lesions.  
  - Dataset bias toward certain demographics.  
  - Lack of multi-modal imaging (e.g., CBCT).  
- **Future Work:**  
  - Integrate 3D volumetric data.  
  - Expand to other dental pathologies (cysts, tumors).




---



*LesionLens — where AI meets dental diagnostics.*
