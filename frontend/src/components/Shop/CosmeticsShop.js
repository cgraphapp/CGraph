import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
export const CosmeticsShop = () => {
    const [cosmetics, setCosmetics] = useState([]);
    const [filter, setFilter] = useState('all');
    const [balance, setBalance] = useState(0);
    const [loading, setLoading] = useState(true);
    useEffect(() => {
        const fetchData = async () => {
            try {
                const response = await fetch('/api/v1/cosmetics/shop', {
                    headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
                });
                const data = await response.json();
                setCosmetics(data.cosmetics || []);
                setBalance(data.user_balance || 0);
            }
            catch (error) {
                toast.error('Failed to load shop');
            }
            finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);
    const handlePurchase = async (cosmeticId, price) => {
        if (balance < price) {
            toast.error('Insufficient credits');
            return;
        }
        try {
            const response = await fetch(`/api/v1/cosmetics/${cosmeticId}/purchase`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${localStorage.getItem('access_token')}`,
                },
            });
            if (!response.ok)
                throw new Error('Purchase failed');
            setBalance(balance - price);
            toast.success('Purchase successful!');
            setCosmetics((prev) => prev.map((c) => (c.id === cosmeticId ? { ...c, owned: true } : c)));
        }
        catch (error) {
            toast.error('Purchase failed');
        }
    };
    const filteredCosmetics = cosmetics.filter((c) => filter === 'all' || c.type === filter);
    if (loading)
        return <div className="text-center py-8">Loading shop...</div>;
    return (<div className="max-w-7xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold text-gray-900 mb-4">Cosmetics Shop</h1>
      
      <div className="mb-8 flex items-center gap-4">
        <div className="bg-blue-100 text-blue-800 px-4 py-2 rounded-lg font-bold">
          💳 Balance: {balance} credits
        </div>
        <button className="bg-green-600 hover:bg-green-700 text-white font-bold py-2 px-6 rounded-lg">
          Add Credits
        </button>
      </div>

      <div className="flex gap-4 mb-8">
        {['all', 'avatar', 'badge', 'effect'].map((type) => (<button key={type} onClick={() => setFilter(type)} className={`px-6 py-2 rounded-lg font-bold transition ${filter === type
                ? 'bg-blue-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'}`}>
            {type.charAt(0).toUpperCase() + type.slice(1)}s
          </button>))}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCosmetics.map((cosmetic) => (<div key={cosmetic.id} className="bg-white rounded-lg shadow-md hover:shadow-lg p-6">
            <div className="w-full h-48 bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center rounded-lg mb-4">
              <img src={cosmetic.image_url} alt={cosmetic.name} className="max-w-full max-h-full object-contain"/>
            </div>

            <h3 className="text-lg font-bold text-gray-900 mb-2">{cosmetic.name}</h3>
            
            <div className="flex items-center justify-between">
              <span className="text-xl font-bold text-blue-600">{cosmetic.price} ✨</span>
              
              {cosmetic.owned ? (<span className="bg-green-100 text-green-800 px-4 py-2 rounded-lg font-bold">✓ Owned</span>) : (<button onClick={() => handlePurchase(cosmetic.id, cosmetic.price)} className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg">
                  Buy
                </button>)}
            </div>
          </div>))}
      </div>
    </div>);
};
