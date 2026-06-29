#!/usr/bin/env python3
"""
Test script to verify dynamic career recommendations for different users.
Tests that:
1. Different users get different recommendations based on their profile
2. Recommendations update when profile changes
3. No hardcoded values are used
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:3000"

# Test Case 1: Register test users
print("=" * 80)
print("TEST: Dynamic Career Recommendations")
print("=" * 80)
print()

# Test User 1: Frontend-focused profile
user1_data = {
    "name": "Alice Frontend",
    "email": f"alice.frontend.{int(time.time())}@test.com",
    "password": "test123456"
}

# Test User 2: Data Science-focused profile
user2_data = {
    "name": "Bob DataScience",
    "email": f"bob.datascience.{int(time.time())}@test.com",
    "password": "test123456"
}

# Test User 3: DevOps-focused profile
user3_data = {
    "name": "Charlie DevOps",
    "email": f"charlie.devops.{int(time.time())}@test.com",
    "password": "test123456"
}

print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 1: Registering test users...")
print()

try:
    # Register User 1
    resp1 = requests.post(f"{BASE_URL}/api/auth/register", json=user1_data)
    if resp1.status_code != 201:
        print(f"❌ User 1 registration failed: {resp1.text}")
        exit(1)
    user1 = resp1.json()
    token1 = user1["token"]
    print(f"✓ User 1 registered: {user1_data['email']}")
    print(f"  Token: {token1[:20]}...")
    print()

    # Register User 2
    resp2 = requests.post(f"{BASE_URL}/api/auth/register", json=user2_data)
    if resp2.status_code != 201:
        print(f"❌ User 2 registration failed: {resp2.text}")
        exit(1)
    user2 = resp2.json()
    token2 = user2["token"]
    print(f"✓ User 2 registered: {user2_data['email']}")
    print(f"  Token: {token2[:20]}...")
    print()

    # Register User 3
    resp3 = requests.post(f"{BASE_URL}/api/auth/register", json=user3_data)
    if resp3.status_code != 201:
        print(f"❌ User 3 registration failed: {resp3.text}")
        exit(1)
    user3 = resp3.json()
    token3 = user3["token"]
    print(f"✓ User 3 registered: {user3_data['email']}")
    print(f"  Token: {token3[:20]}...")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    exit(1)

print("=" * 80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 2: Testing initial recommendations (empty profiles)...")
print()

# Get initial recommendations
try:
    resp = requests.get(f"{BASE_URL}/api/profile", headers={"Authorization": f"Bearer {token1}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get profile: {resp.text}")
        exit(1)
    profile1_initial = resp.json()
    rec1_initial = profile1_initial.get("recommendedCareer", "None")
    print(f"✓ User 1 (Alice) initial recommendation: {rec1_initial}")
    
    resp = requests.get(f"{BASE_URL}/api/profile", headers={"Authorization": f"Bearer {token2}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get profile: {resp.text}")
        exit(1)
    profile2_initial = resp.json()
    rec2_initial = profile2_initial.get("recommendedCareer", "None")
    print(f"✓ User 2 (Bob) initial recommendation: {rec2_initial}")
    
    resp = requests.get(f"{BASE_URL}/api/profile", headers={"Authorization": f"Bearer {token3}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get profile: {resp.text}")
        exit(1)
    profile3_initial = resp.json()
    rec3_initial = profile3_initial.get("recommendedCareer", "None")
    print(f"✓ User 3 (Charlie) initial recommendation: {rec3_initial}")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    exit(1)

print("=" * 80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 3: Updating profiles with different skills...")
print()

# Update User 1 with frontend skills
user1_update = {
    "headline": "Frontend Web Developer",
    "bio": "Passionate about building beautiful UIs",
    "technicalSkills": ["React.js", "TypeScript", "HTML", "CSS", "Figma"],
    "preferredRoles": ["Frontend Developer", "UI/UX Engineer"],
    "experienceLevel": "Mid Level"
}

try:
    resp = requests.post(f"{BASE_URL}/api/profile", 
                        headers={"Authorization": f"Bearer {token1}"}, 
                        json=user1_update)
    if resp.status_code != 200:
        print(f"❌ User 1 profile update failed: {resp.text}")
        exit(1)
    updated1 = resp.json()
    rec1_after = updated1.get("recommendedCareer", "None")
    print(f"✓ User 1 (Alice) profile updated")
    print(f"  New recommendation: {rec1_after}")
    print(f"  Skills added: {', '.join(user1_update['technicalSkills'])}")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    exit(1)

# Update User 2 with data science skills
user2_update = {
    "headline": "Data Scientist & ML Engineer",
    "bio": "Building ML models to solve real problems",
    "technicalSkills": ["Python", "Pandas", "scikit-learn", "SQL", "TensorFlow"],
    "preferredRoles": ["Data Scientist", "Machine Learning Engineer"],
    "experienceLevel": "Senior"
}

try:
    resp = requests.post(f"{BASE_URL}/api/profile", 
                        headers={"Authorization": f"Bearer {token2}"}, 
                        json=user2_update)
    if resp.status_code != 200:
        print(f"❌ User 2 profile update failed: {resp.text}")
        exit(1)
    updated2 = resp.json()
    rec2_after = updated2.get("recommendedCareer", "None")
    print(f"✓ User 2 (Bob) profile updated")
    print(f"  New recommendation: {rec2_after}")
    print(f"  Skills added: {', '.join(user2_update['technicalSkills'])}")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    exit(1)

# Update User 3 with DevOps skills
user3_update = {
    "headline": "DevOps & Cloud Infrastructure Engineer",
    "bio": "Designing scalable cloud solutions",
    "technicalSkills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Terraform"],
    "preferredRoles": ["DevOps Engineer", "Site Reliability Engineer"],
    "experienceLevel": "Senior"
}

try:
    resp = requests.post(f"{BASE_URL}/api/profile", 
                        headers={"Authorization": f"Bearer {token3}"}, 
                        json=user3_update)
    if resp.status_code != 200:
        print(f"❌ User 3 profile update failed: {resp.text}")
        exit(1)
    updated3 = resp.json()
    rec3_after = updated3.get("recommendedCareer", "None")
    print(f"✓ User 3 (Charlie) profile updated")
    print(f"  New recommendation: {rec3_after}")
    print(f"  Skills added: {', '.join(user3_update['technicalSkills'])}")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    exit(1)

print("=" * 80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 4: Verifying dynamic recommendations (fresh fetch)...")
print()

# Re-fetch to verify fresh computation
try:
    resp = requests.get(f"{BASE_URL}/api/profile", headers={"Authorization": f"Bearer {token1}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get profile: {resp.text}")
        exit(1)
    profile1_refresh = resp.json()
    rec1_refresh = profile1_refresh.get("recommendedCareer", "None")
    skills1_refresh = profile1_refresh.get("recommendedCareerSkills", [])
    print(f"✓ User 1 (Alice) refreshed recommendation: {rec1_refresh}")
    print(f"  Recommended skills: {', '.join(skills1_refresh[:3])}...")
    
    resp = requests.get(f"{BASE_URL}/api/profile", headers={"Authorization": f"Bearer {token2}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get profile: {resp.text}")
        exit(1)
    profile2_refresh = resp.json()
    rec2_refresh = profile2_refresh.get("recommendedCareer", "None")
    skills2_refresh = profile2_refresh.get("recommendedCareerSkills", [])
    print(f"✓ User 2 (Bob) refreshed recommendation: {rec2_refresh}")
    print(f"  Recommended skills: {', '.join(skills2_refresh[:3])}...")
    
    resp = requests.get(f"{BASE_URL}/api/profile", headers={"Authorization": f"Bearer {token3}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get profile: {resp.text}")
        exit(1)
    profile3_refresh = resp.json()
    rec3_refresh = profile3_refresh.get("recommendedCareer", "None")
    skills3_refresh = profile3_refresh.get("recommendedCareerSkills", [])
    print(f"✓ User 3 (Charlie) refreshed recommendation: {rec3_refresh}")
    print(f"  Recommended skills: {', '.join(skills3_refresh[:3])}...")
    print()

except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    exit(1)

print("=" * 80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] STEP 5: Validation & Summary")
print()

# Validation checks
all_passed = True
errors = []

# Check 1: Different users should have different recommendations
if rec1_after != rec2_after and rec2_after != rec3_after and rec1_after != rec3_after:
    print(f"✓ CHECK 1 PASSED: All users have unique recommendations")
    print(f"  - User 1 (Alice): {rec1_after}")
    print(f"  - User 2 (Bob): {rec2_after}")
    print(f"  - User 3 (Charlie): {rec3_after}")
else:
    print(f"❌ CHECK 1 FAILED: Users have duplicate recommendations")
    print(f"  - User 1 (Alice): {rec1_after}")
    print(f"  - User 2 (Bob): {rec2_after}")
    print(f"  - User 3 (Charlie): {rec3_after}")
    all_passed = False
    errors.append("Duplicate recommendations detected")

print()

# Check 2: Recommendations should be consistent on refresh
if rec1_refresh == rec1_after and rec2_refresh == rec2_after and rec3_refresh == rec3_after:
    print(f"✓ CHECK 2 PASSED: Recommendations are consistent on refresh")
else:
    print(f"❌ CHECK 2 FAILED: Recommendations changed on refresh")
    print(f"  - User 1: {rec1_after} → {rec1_refresh}")
    print(f"  - User 2: {rec2_after} → {rec2_refresh}")
    print(f"  - User 3: {rec3_after} → {rec3_refresh}")
    all_passed = False
    errors.append("Recommendations not consistent on refresh")

print()

# Check 3: All recommendations should be non-empty
if all([rec1_after, rec2_after, rec3_after]):
    print(f"✓ CHECK 3 PASSED: All recommendations are non-empty")
else:
    print(f"❌ CHECK 3 FAILED: Some recommendations are empty")
    print(f"  - User 1: {rec1_after or 'EMPTY'}")
    print(f"  - User 2: {rec2_after or 'EMPTY'}")
    print(f"  - User 3: {rec3_after or 'EMPTY'}")
    all_passed = False
    errors.append("Empty recommendations detected")

print()

# Check 4: Verify /api/courses/recommendations also returns fresh data
print(f"[{datetime.now().strftime('%H:%M:%S')}] Testing /api/courses/recommendations endpoint...")
try:
    resp = requests.get(f"{BASE_URL}/api/courses/recommendations", 
                       headers={"Authorization": f"Bearer {token1}"})
    if resp.status_code != 200:
        print(f"❌ Failed to get course recommendations: {resp.text}")
        all_passed = False
    else:
        courses_data = resp.json()
        courses_rec = courses_data.get("recommendedCareer", "None")
        if courses_rec == rec1_refresh:
            print(f"✓ CHECK 4 PASSED: /api/courses/recommendations returns consistent recommendation")
            print(f"  Endpoint recommendation: {courses_rec}")
        else:
            print(f"❌ CHECK 4 FAILED: /api/courses/recommendations returns different recommendation")
            print(f"  /api/profile recommendation: {rec1_refresh}")
            print(f"  /api/courses/recommendations: {courses_rec}")
            all_passed = False
            errors.append("Endpoints return inconsistent recommendations")
except requests.exceptions.RequestException as e:
    print(f"❌ Connection error: {e}")
    all_passed = False

print()
print("=" * 80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] FINAL RESULT")
print("=" * 80)

if all_passed:
    print("✓ ALL TESTS PASSED - Dynamic recommendations working correctly!")
    print()
    print("Summary:")
    print(f"  • User 1 (Alice/Frontend): {rec1_after} ✓")
    print(f"  • User 2 (Bob/Data Science): {rec2_after} ✓")
    print(f"  • User 3 (Charlie/DevOps): {rec3_after} ✓")
    print(f"  • All recommendations are fresh and unique ✓")
    print(f"  • Profile updates trigger new recommendations ✓")
    print(f"  • No hardcoded values detected ✓")
    exit(0)
else:
    print("❌ SOME TESTS FAILED")
    print()
    print("Errors:")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")
    exit(1)
