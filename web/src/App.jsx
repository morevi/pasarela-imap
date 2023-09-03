import { useEffect, useState } from "react";
import "./App.scss";
import { EyeSlashIcon, TrashIcon, FolderIcon } from "@heroicons/react/24/solid";
import { v4 as uuidv4 } from "uuid";

const API_URL = "https://192.168.1.138";

function baFetch(url, email, pwd, method = "GET") {
  let headers = new Headers();
  headers.append("Authorization", "Basic " + btoa(email + ":" + pwd));

  return fetch(url, {
    headers: headers,
    method: method,
  });
}

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [pwd, setPwd] = useState("");
  const [ok, setOk] = useState(true);

  const handleClick = async () => {
    console.log(email, pwd);
    if (!email || !pwd) {
      setOk(false);
      return;
    }

    const response = await baFetch(API_URL, email, pwd);
    if (response.status !== 200) {
      const message = await response.json();
      console.log("error", message);
      setOk(false);
      return;
    }

    const directories = await response.json();
    setOk(true);
    onLogin(email, pwd, directories);
  };

  return (
    <nav className="navbar navbar-expand-lg justify-content-between p-2 shadow bg-light">
      <a className="navbar-brand mr-auto" href="#">
        Pasarela IMAP
      </a>

      <div className="d-flex ml-auto">
        <input
          className="form-control me-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <input
          className="form-control me-2"
          type="password"
          placeholder="Password"
          value={pwd}
          onChange={(e) => setPwd(e.target.value)}
        />
        <button
          className={"btn " + (ok ? "btn-primary" : "btn-danger")}
          onClick={handleClick}
        >
          Login
        </button>
      </div>
    </nav>
  );
}

function Dirs({ dirs, onDirClick }) {
  const [selected, setSelected] = useState(dirs[0]);

  if (!dirs || dirs.length === 0) {
    return (
      <div className="border m-3 p-3 w-25 shadow">
        <h3>Folders</h3>
        <p>No folders to show</p>
      </div>
    );
  }

  const handleDirClick = async (dir) => {
    setSelected(dir);
    onDirClick(dir);
  };

  return (
    <div className="border m-3 p-3 w-25 text-truncate shadow">
      <h3>Folders</h3>
      <table className="table table-hover">
        <thead>
          <tr>
            <th></th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {dirs.map((dir) => (
            <tr>
              <td>
                <FolderIcon className="sm-icon" />
              </td>
              <td
                className={dir === selected ? "text-primary " : ""}
                onClick={() => handleDirClick(dir)}
                key={dir}
              >
                {dir}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

const MailRow = ({ mail, selected, onMailClick, onUnread, onDelete }) => {
  let color = "";

  if (mail.uid === selected) {
    color = "text-primary";
  } else if (mail.flags.includes("\\Seen")) {
    color = "text-secondary";
  }

  return (
    <tr key={mail.uid}>
      <td
        className={color}
        key={uuidv4()}
        onClick={() => onMailClick(mail.uid)}
      >
        {mail.from}
      </td>
      <td
        className={color}
        key={uuidv4()}
        onClick={() => onMailClick(mail.uid)}
      >
        {mail.subject}
      </td>
      <td key={uuidv4()}>
        <div className="d-flex text-right">
          <TrashIcon className="sm-icon" onClick={() => onDelete(mail.uid)} />
          <EyeSlashIcon
            className="sm-icon"
            onClick={() => onUnread(mail.uid)}
          />
        </div>
      </td>
    </tr>
  );
};

function MailList({ mails, onMailClick, onUnread, onDelete }) {
  const [selected, setSelected] = useState("");

  if (!mails || mails.length === 0) {
    return (
      <>
        <div className="border m-3 p-3 w-50 shadow">
          <h3>Your mail</h3>
          <p>No mails to show</p>
        </div>
      </>
    );
  }

  const handleMailClick = async (uid) => {
    setSelected(uid);
    console.log("selected", uid);
    onMailClick(uid);
  };

  return (
    <div className="border m-3 p-3 w-50 shadow">
      <h3>Your mail</h3>
      <table className="table table-hover">
        <thead>
          <tr>
            <th scope="col">From</th>
            <th scope="col">Subject</th>
            <th scope="col">Actions</th>
          </tr>
        </thead>
        <tbody>
          {mails.map((mail) => (
            <MailRow
              key={mail.uid}
              mail={mail}
              selected={selected}
              onMailClick={handleMailClick}
              onDelete={onDelete}
              onUnread={onUnread}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Link({ attachment, onAttachmentClick }) {
  return (
    <>
      <button
        className="btn btn-link"
        onClick={() => onAttachmentClick(attachment)}
      >
        <span>{attachment.filename}</span>
      </button>
    </>
  );
}

function MailView({ mail = {}, onAttachmentClick }) {
  if (mail.uid === undefined) {
    return (
      <>
        <div className="border m-3 p-3 w-50 shadow">
          <h3>Mail view</h3>
          <p>No mail to show</p>
        </div>
      </>
    );
  }

  return (
    <div className="border m-3 p-3 w-50 shadow">
      <h3>Mail view</h3>
      <div>
        <div className=" mb-5">
          <div className="mb-3">
            From <span className="badge text-bg-primary fs-6">{mail.from}</span>{" "}
            for <span className="badge text-bg-success fs-6">{mail.to}</span> at{" "}
            {mail.date}
          </div>
          <h5>{mail.subject}</h5>
          <div>
            {mail.attachments && mail.attachments.length
              ? mail.attachments.map((att) => (
                  <Link
                    key={att.link}
                    attachment={att}
                    onAttachmentClick={onAttachmentClick}
                  />
                ))
              : ""}
          </div>
        </div>

        <div className="display-linebreak"> {mail.text}</div>
      </div>
    </div>
  );
}

function App() {
  const [email, setEmail] = useState("");
  const [pwd, setPwd] = useState("");

  const [dirs, setDirs] = useState([]);
  const [dir, setDir] = useState("");

  const [mails, setMails] = useState([]);
  const [mail, setMail] = useState({});

  const handleLogin = (email, pwd, dirs) => {
    setEmail(email);
    setPwd(pwd);
    setDirs(dirs);
  };

  const handleDirClick = async (dir) => {
    if (!dir) {
      return;
    }

    if (!email || !pwd) {
      setMails([]);
    }

    const response = await baFetch(
      API_URL + "/" + dir + "?page_size=50",
      email,
      pwd
    );
    if (response.status === 401) {
      console.log("Unauthorized");
      return;
    }
    const mails = (await response.json()).mails;

    setDir(dir);
    setMails(mails);
  };

  const handleMailClick = async (uid) => {
    if (!uid) {
      return;
    }

    if (!email || !pwd) {
      setUID("");
    }

    const response = await baFetch(API_URL + "/" + dir + "/" + uid, email, pwd);
    if (response.status === 401) {
      console.log("Unauthorized");
      return;
    }
    const mail = await response.json();
    setMail(mail);

    // mark as read without fetching all mails again
    for (let i = 0; i < mails.length; i++) {
      if (mails[i].uid === uid) {
        mails[i].flags.push("\\Seen");
        break;
      }
    }
  };

  const handleAttachmentClick = async (att) => {
    if (!att.filename || !att.link) {
      return;
    }

    const response = await baFetch(API_URL + att.link, email, pwd);
    if (response.status === 401) {
      console.log("Unauthorized");
      return;
    }

    const res = await response.blob();

    // create 'a', click it and delete it
    const aElement = document.createElement("a");
    aElement.setAttribute("download", att.filename);
    const href = URL.createObjectURL(res);
    aElement.href = href;
    aElement.setAttribute("target", "_blank");
    aElement.click();
    URL.revokeObjectURL(href);
  };

  const handleDelete = async (uid) => {
    console.log("delete", uid);
    const response = await baFetch(
      API_URL + "/" + dir + "/" + uid,
      email,
      pwd,
      "DELETE"
    );
    if (response.status === 401) {
      console.log("Unauthorized");
      return;
    }
    let newMails = [...mails];
    for (let i = 0; i < mails.length; i++) {
      if (mails[i].uid === uid) {
        newMails.splice(i, 1);
        break;
      }
    }
    setMails(newMails);
  };

  const handleUnread = async (uid) => {
    console.log("unread", uid);

    const url = API_URL + "/" + dir + "/" + uid + "?unsee=1";
    const response = await baFetch(url, email, pwd, "PUT");
    if (response.status === 401) {
      console.log("Unauthorized");
      return;
    }

    // mark as read without fetching all mails again
    for (let i = 0; i < mails.length; i++) {
      if (mails[i].uid === uid) {
        mails[i].flags = mails[i].flags.filter((f) => f !== "\\Seen");
        break;
      }
    }
  };

  return (
    <div>
      <Login onLogin={handleLogin} />
      <div className="d-flex w-100">
        <Dirs dirs={dirs} onDirClick={handleDirClick} />
        <MailList
          mails={mails}
          onMailClick={handleMailClick}
          onDelete={handleDelete}
          onUnread={handleUnread}
        />
        <MailView mail={mail} onAttachmentClick={handleAttachmentClick} />
      </div>
    </div>
  );
}

export default App;
