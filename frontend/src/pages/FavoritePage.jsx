import React from "react";
import FavoriteView from "../components/FavoriteView";

const FavoritePage = () => {
  return (
    <div className="min-h-screen bg-gray-800 text-gray-200">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <FavoriteView />
      </div>
    </div>
  );
};

export default FavoritePage;
