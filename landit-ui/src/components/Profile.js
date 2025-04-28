import React, { useState } from 'react';

const Profile = ({ userInfo, setUserInfo }) => {
    const [editing, setEditing] = useState(false);

    const handleChange = (e) => {
        setUserInfo({
            ...userInfo,
            [e.target.name]: e.target.value
        });
    };

    return (
        <div style={{ marginTop: '2rem' }}>
            <h2>👤 Your Profile</h2>

            {editing ? (
                <>
                    <input
                        type="text"
                        name="fullName"
                        placeholder="Full Name"
                        value={userInfo.fullName}
                        onChange={handleChange}
                    /><br/>
                    <input
                        type="text"
                        name="age"
                        placeholder="Age"
                        value={userInfo.age}
                        onChange={handleChange}
                    /><br/>
                    <input
                        type="text"
                        name="profession"
                        placeholder="Profession"
                        value={userInfo.profession}
                        onChange={handleChange}
                    /><br/>
                    <input
                        type="text"
                        name="country"
                        placeholder="Country"
                        value={userInfo.country}
                        onChange={handleChange}
                    /><br/>
                    <button onClick={() => setEditing(false)}>Save Profile</button>
                </>
            ) : (
                <>
                    <p><strong>Full Name:</strong> {userInfo.fullName}</p>
                    <p><strong>Age:</strong> {userInfo.age}</p>
                    <p><strong>Profession:</strong> {userInfo.profession}</p>
                    <p><strong>Country:</strong> {userInfo.country}</p>
                    <button onClick={() => setEditing(true)}>Edit Profile</button>
                </>
            )}
        </div>
    );
};

export default Profile;
