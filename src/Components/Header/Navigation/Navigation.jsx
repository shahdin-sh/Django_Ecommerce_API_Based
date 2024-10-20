import { HiMiniBars3 } from "react-icons/hi2";
import { VscAccount } from "react-icons/vsc";
import { Link } from "react-router-dom";
import NavMenu from "./NavMenu";
import { useEffect, useState } from "react";

const Navigation = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isScrollingDisabled, setIsScrollingDisabled] = useState(false);

  // menu open function
  const clickHandler = () => {
    setIsOpen(!isOpen);
    setIsScrollingDisabled(true);
  };

  // desabling scroll while menu is open
  const preventScroll = (e) => {
    if (isScrollingDisabled) {
      e.preventDefault();
    }
  };

  useEffect(() => {
    // Add event listener to prevent scrolling
    window.addEventListener("wheel", preventScroll, { passive: false });
    window.addEventListener("touchmove", preventScroll, { passive: false });

    // Cleanup function to remove the event listener
    return () => {
      window.removeEventListener("wheel", preventScroll);
      window.removeEventListener("touchmove", preventScroll);
    };
  }, [isScrollingDisabled]);

  return (
    <>
      <nav className="w-full h-full flexRow justify-end items-center gap-[30px]">
        {/* account link */}
        <Link to="/" className="w-[24px] h-[24px] flex justify-center items-center">
          <VscAccount className="w-full h-full" />
        </Link>

        {/* open menu button */}
        <button onClick={clickHandler} className="w-[30px] h-[30px] flex justify-center items-center">
          <HiMiniBars3 className="w-full h-full" />
        </button>

        {/* menu items */}
        {isOpen && <NavMenu isOpen={isOpen} setIsOpen={setIsOpen} setIsScrollingDisabled={setIsScrollingDisabled} />}
      </nav>
    </>
  );
};

export default Navigation;
