import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

interface Avatar {
  id: string;
  name: string;
  preview_url: string;
  owned: boolean;
}

interface AvatarSelectorProps {
  onSelect: (avatarId: string) => void;
}

export const AvatarSelector: React.FC<AvatarSelectorProps> = ({ onSelect }) => {
  const [avatars, setAvatars] = useState<Avatar[]>([]);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    const fetchAvatars = async () => {
      try {
        const response = await fetch('/api/v1/cosmetics/avatars', {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        });
        const data = await response.json();
        setAvatars(data.avatars || []);
      } catch (error) {
        toast.error('Failed to load avatars');
      }
    };

    fetchAvatars();
  }, []);

  const handleSelect = (avatarId: string) => {
    setSelected(avatarId);
    onSelect(avatarId);
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow-md">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Choose Avatar</h3>
      
      <div className="grid grid-cols-3 md:grid-cols-4 gap-4">
        {avatars.map((avatar) => (
          <button
            key={avatar.id}
            onClick={() => handleSelect(avatar.id)}
            className={`relative rounded-lg overflow-hidden border-2 transition ${
              selected === avatar.id
                ? 'border-blue-600 shadow-lg'
                : 'border-gray-300 hover:border-blue-400'
            }`}
          >
            <img
              src={avatar.preview_url}
              alt={avatar.name}
              className="w-full h-auto"
            />
            
            {!avatar.owned && (
              <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                <span className="text-white font-bold">🔒 Locked</span>
              </div>
            )}
          </button>
        ))}
      </div>

      {selected && (
        <button className="mt-4 w-full bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-4 rounded-lg transition">
          Confirm Selection
        </button>
      )}
    </div>
  );
};

