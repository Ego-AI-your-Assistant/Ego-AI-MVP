import React, { useState, useEffect } from 'react';
import './Profile.css';

interface UserProfile {
  name: string;
  surname: string;
  hometown: string;
  sex: 'male' | 'female' | 'other' | '';
  age: string;
  description: string;
}

export const Profile: React.FC = () => {
  const [profile, setProfile] = useState<UserProfile>({
    name: '',
    surname: '',
    hometown: '',
    sex: '',
    age: '',
    description: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSaved, setIsSaved] = useState(false);

  // Load profile data on component mount
  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setIsLoading(true);
      const useBackend = import.meta.env.VITE_BACKEND_USE !== 'false';
      
      if (useBackend) {
        const response = await fetch('/api/v1/profile/users/profile');
        if (response.ok) {
          const data = await response.json();
          setProfile(data);
        }
      } else {
        // Mock data for development
        const mockProfile = {
          name: 'John',
          surname: 'Doe',
          hometown: 'Moscow',
          sex: 'male' as const,
          age: '28',
          description: 'Software developer passionate about creating innovative solutions and exploring new technologies.'
        };
        setProfile(mockProfile);
      }
    } catch (error) {
      console.error('Error loading profile:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: keyof UserProfile, value: string) => {
    setProfile(prev => ({
      ...prev,
      [field]: value
    }));
    setIsSaved(false);
  };

  const handleSave = async () => {
    try {
      setIsLoading(true);
      const useBackend = import.meta.env.VITE_BACKEND_USE !== 'false';
      
      if (useBackend) {
        const response = await fetch('/api/v1/profile/users/profile', {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(profile)
        });
        
        if (response.ok) {
          setIsSaved(true);
          setTimeout(() => setIsSaved(false), 3000);
        } else {
          throw new Error('Failed to save profile');
        }
      } else {
        // Mock save for development
        setTimeout(() => {
          setIsSaved(true);
          setTimeout(() => setIsSaved(false), 3000);
        }, 1000);
      }
    } catch (error) {
      console.error('Error saving profile:', error);
      alert('Error saving profile. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const isFormValid = profile.name.trim() && profile.surname.trim() && profile.age.trim();

  return (
    <div className="profile-container">
      <div className="profile-content">
        <div className="profile-card">
          <div className="profile-header">
            <h1 className="profile-title">Personal Information</h1>
            <p className="profile-subtitle">Update your personal details</p>
          </div>

          <div className="profile-form">
            <div className="form-section">
              <h3 className="section-title">Personal Information</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="name" className="form-label">
                    First Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    id="name"
                    className="form-input"
                    placeholder="John"
                    value={profile.name}
                    onChange={(e) => handleInputChange('name', e.target.value)}
                    disabled={isLoading}
                    autoComplete="given-name"
                    maxLength={50}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="surname" className="form-label">
                    Last Name <span className="required">*</span>
                  </label>
                  <input
                    type="text"
                    id="surname"
                    className="form-input"
                    placeholder="Doe"
                    value={profile.surname}
                    onChange={(e) => handleInputChange('surname', e.target.value)}
                    disabled={isLoading}
                    autoComplete="family-name"
                    maxLength={50}
                  />
                </div>
              </div>
            </div>

            <div className="form-section">
              <h3 className="section-title">Demographics</h3>
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="age" className="form-label">
                    Age <span className="required">*</span>
                  </label>
                  <input
                    type="number"
                    id="age"
                    className="form-input age-input"
                    placeholder="25"
                    min="13"
                    max="120"
                    value={profile.age}
                    onChange={(e) => handleInputChange('age', e.target.value)}
                    disabled={isLoading}
                  />
                  <span className="field-hint">Must be 13 or older</span>
                </div>
                <div className="form-group">
                  <label htmlFor="sex" className="form-label">Gender</label>
                  <div className="radio-group">
                    <div className="radio-option">
                      <input
                        type="radio"
                        id="male"
                        name="sex"
                        value="male"
                        checked={profile.sex === 'male'}
                        onChange={(e) => handleInputChange('sex', e.target.value)}
                        disabled={isLoading}
                      />
                      <label htmlFor="male" className="radio-label">Male</label>
                    </div>
                    <div className="radio-option">
                      <input
                        type="radio"
                        id="female"
                        name="sex"
                        value="female"
                        checked={profile.sex === 'female'}
                        onChange={(e) => handleInputChange('sex', e.target.value)}
                        disabled={isLoading}
                      />
                      <label htmlFor="female" className="radio-label">Female</label>
                    </div>
                    <div className="radio-option">
                      <input
                        type="radio"
                        id="other"
                        name="sex"
                        value="other"
                        checked={profile.sex === 'other'}
                        onChange={(e) => handleInputChange('sex', e.target.value)}
                        disabled={isLoading}
                      />
                      <label htmlFor="other" className="radio-label">Other</label>
                    </div>
                    <div className="radio-option">
                      <input
                        type="radio"
                        id="prefer-not-to-say"
                        name="sex"
                        value=""
                        checked={profile.sex === ''}
                        onChange={(e) => handleInputChange('sex', e.target.value)}
                        disabled={isLoading}
                      />
                      <label htmlFor="prefer-not-to-say" className="radio-label">Prefer not to say</label>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="form-section">
              <h3 className="section-title">Location</h3>
              <div className="form-group">
                <label htmlFor="hometown" className="form-label">Hometown</label>
                <input
                  type="text"
                  id="hometown"
                  className="form-input"
                  placeholder="New York, NY"
                  value={profile.hometown}
                  onChange={(e) => handleInputChange('hometown', e.target.value)}
                  disabled={isLoading}
                  autoComplete="address-level2"
                  maxLength={100}
                />
                <span className="field-hint">City, State/Country</span>
              </div>
            </div>

            <div className="form-section">
              <h3 className="section-title">About</h3>
              <div className="form-group">
                <label htmlFor="description" className="form-label">Self Description</label>
                <div className="textarea-container">
                  <textarea
                    id="description"
                    className="form-textarea"
                    placeholder="Tell us about yourself..."
                    rows={4}
                    value={profile.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    disabled={isLoading}
                    maxLength={500}
                  />
                  <div className="character-count">
                    {profile.description.length}/500
                  </div>
                </div>
              </div>
            </div>

            <div className="form-actions">
              <button
                className="save-button"
                onClick={handleSave}
                disabled={isLoading || !isFormValid}
              >
                {isLoading ? (
                  <>
                    <div className="loading-spinner"></div>
                    Saving...
                  </>
                ) : (
                  'Save Profile'
                )}
              </button>
              
              {isSaved && (
                <div className="save-success">
                  ✓ Profile saved successfully!
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}; 