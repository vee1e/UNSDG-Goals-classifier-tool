import React from "react";
import Image from "next/image";
import Logo from "@/assets/GW Open Source Program Office.png";

/*
Header Component
- Displays the application header with logo
*/

const Header = () => {
  return (
    <header className="p-6">
      <div className="flex items-center">
        <Image
          src={Logo}
          alt="Logo"
          width={60}
          height={60}
          className="rounded-lg"
        />
      </div>
    </header>
  );
};

export default Header;
