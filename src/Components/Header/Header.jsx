import { Link } from "react-router-dom";
import logo from "../../../public/images/logo/logo.svg";
import SearchBar from "./SearchBar/SearchBar";
import Navigation from "./Navigation/Navigation";
import { useEffect, useRef, useState } from "react";

import classes from "./styles.module.css";

const Header = () => {
  const [scrolled, setScrolled] = useState(false);
  const ref = useRef();

  // header scroll event function
  useEffect(() => {
    const handleScroll = () => {
      if (window.scrollY >= 90 && !scrolled) {
        setScrolled(true);
        ref.current.classList.remove("bg-[rgb(241,241,241)]");
        ref.current.classList.add("sticky", "top-0", "bg-white", classes.fadeIn);
      } else if (window.scrollY === 0) {
        ref.current.classList.remove("sticky", "top-0", classes.fadeIn);
      } else if (window.scrollY < 90 && scrolled) {
        setScrolled(false);
        ref.current.classList.remove("bg-white");
        ref.current.classList.add("bg-[rgb(241,241,241)]");
      }
    };

    window.addEventListener("scroll", handleScroll);

    // Cleanup the event listener when the component unmounts
    return () => window.removeEventListener("scroll", handleScroll);
  }, [scrolled]);

  return (
    <>
      <header ref={ref} className="w-full h-[90px] flexRow justify-center items-center bg-[rgb(241,241,241)] z-50 duration-300">
        <div className="wrapper w-full h-full flexRow justify-between items-center">
          {/* search bar */}
          <SearchBar />

          {/* logo */}
          <div className="w-full h-full flex justify-center items-center">
            <Link to="/" className="h-fit p-[8px]">
              <img src={logo} alt="logo" />
            </Link>
          </div>

          {/* navigation */}
          <Navigation />
        </div>
      </header>
    </>
  );
};

export default Header;
