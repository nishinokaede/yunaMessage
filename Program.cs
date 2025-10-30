using Newtonsoft.Json;
using System.IO;
using System.IO.Compression;
using System.Net;
using System.Text;

namespace DownMessageFor46
{
    internal class Program
    {
        public static bool nogiConfig = true;
        public static bool sakuConfig = true;
        public static bool hinaConfig = true;

        public static MemberToken nogiMemberToken = new();
        public static MemberToken sakuMemberToken = new();
        public static MemberToken hinaMemberToken = new();

        static void Main(string[] args)
        {
            if (!Directory.Exists("log"))
            {
                Directory.CreateDirectory("log");
            }
            #region 检查配置文件是否存在 读取配置文件
            if (!File.Exists("config\\nogiConfig.json"))
            {
                AddLog("没有检测到乃木坂的配置文件", true);
                nogiConfig = false;
            }
            else
            {
                try
                {
                    ConfigRead nogi = JsonConvert.DeserializeObject<ConfigRead>(System.IO.File.ReadAllText("config\\nogiConfig.json"));
                    nogiMemberToken.rootPath = nogi.rootPath;
                    nogiMemberToken.RefreshToken = nogi.token;
                    nogiMemberToken.memberLists = nogi.member;
                    AddLog("读取乃木坂配置文件成功！");
                }
                catch (Exception ex)
                {
                    AddLog("读取乃木坂配置文件失败，可能因为配置文件格式错误" + ex.Message + ex.StackTrace, true);
                }
            }
            if (!File.Exists("config\\sakuConfig.json"))
            {
                AddLog("没有检测到櫻坂的配置文件", true);
                sakuConfig = false;
            }
            else
            {
                try
                {
                    ConfigRead saku = JsonConvert.DeserializeObject<ConfigRead>(System.IO.File.ReadAllText("config\\sakuConfig.json"));
                    sakuMemberToken.rootPath = saku.rootPath;
                    sakuMemberToken.RefreshToken = saku.token;
                    sakuMemberToken.memberLists = saku.member;
                }
                catch (Exception ex)
                {
                    AddLog("读取櫻坂配置文件失败，可能因为配置文件格式错误" + ex.Message + ex.StackTrace, true);
                }
            }
            if (!File.Exists("config\\hinaConfig.json"))
            {
                AddLog("没有检测到日向坂的配置文件", true);
                hinaConfig = false;
            }
            else
            {
                try
                {
                    ConfigRead hina = JsonConvert.DeserializeObject<ConfigRead>(System.IO.File.ReadAllText("config\\hinaConfig.json"));
                    hinaMemberToken.rootPath = hina.rootPath;
                    hinaMemberToken.RefreshToken = hina.token;
                    hinaMemberToken.memberLists = hina.member;
                }
                catch (Exception ex)
                {
                    AddLog("读取日向坂配置文件失败，可能因为配置文件格式错误" + ex.Message + ex.StackTrace, true);
                }
            }
            #endregion
            GetToken();
            if (nogiConfig)
            {
                GetMessage(nogiMemberToken, "nogi");
            }
            if (sakuConfig)
            {
                GetMessage(sakuMemberToken, "saku");
            }
            if (hinaConfig)
            {
                GetMessage(hinaMemberToken, "hina");
            }
            Console.WriteLine("按任意键结束");
            Console.ReadKey();
        }

        /// <summary>
        /// 拿到token 保存到各自的类中
        /// </summary>
        public static void GetToken()
        {
            if (nogiConfig)
            {
                try
                {
                    string uploadurl = "https://api.n46.glastonr.net/v2/update_token";
                    string refreshtoken = "{\"refresh_token\":\"" + nogiMemberToken.RefreshToken + "\"}";
                    byte[] postData = Encoding.UTF8.GetBytes(refreshtoken);
                    var webclient = new WebClient();
                    webclient.Headers.Clear();
                    webclient.Headers.Add("Accept", "application/json");
                    webclient.Headers.Add("Content-Type", "application/json");
                    webclient.Headers.Add("X-Talk-App-ID", "jp.co.sonymusic.communication.nogizaka 2.4");
                    webclient.Headers.Add("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)");
                    webclient.Headers.Add("Accept-Language", "ja-JP");
                    webclient.Headers.Add("Accept-Encoding", "gzip");
                    //webclient.Headers.Add("Connection", "Keep-Alive");
                    webclient.Headers.Add("TE", "gzip, deflate; q=0.5");
                    byte[] responseData = webclient.UploadData(uploadurl, "POST", postData);
                    string access_token = Encoding.UTF8.GetString(responseData);
                    Rrefreshtoken json = JsonConvert.DeserializeObject<Rrefreshtoken>(access_token);
                    nogiMemberToken.AccessToken = json.access_token;
                    AddLog("乃木坂-临时TOKEN获取成功！");

                }
                catch (Exception ex)
                {
                    AddLog("乃木坂-临时TOKEN获取失败" + ex.Message + ex.StackTrace);
                }
            }
            if (sakuConfig)
            {
                try
                {
                    string uploadurl = "https://api.s46.glastonr.net/v2/update_token";
                    string refreshtoken = "{\"refresh_token\":\"" + sakuMemberToken.RefreshToken + "\"}";
                    byte[] postData = Encoding.UTF8.GetBytes(refreshtoken);
                    var webclient = new WebClient();
                    webclient.Headers.Clear();
                    webclient.Headers.Add("Accept", "application/json");
                    webclient.Headers.Add("Content-Type", "application/json");
                    webclient.Headers.Add("X-Talk-App-ID", "jp.co.sonymusic.communication.sakurazaka 2.4");
                    webclient.Headers.Add("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)");
                    webclient.Headers.Add("Accept-Language", "ja-JP");
                    webclient.Headers.Add("Accept-Encoding", "gzip");
                    //webclient.Headers.Add("Connection", "Keep-Alive");
                    webclient.Headers.Add("TE", "gzip, deflate; q=0.5");
                    byte[] responseData = webclient.UploadData(uploadurl, "POST", postData);
                    string access_token = Encoding.UTF8.GetString(responseData);
                    Rrefreshtoken json = JsonConvert.DeserializeObject<Rrefreshtoken>(access_token);
                    sakuMemberToken.AccessToken = json.access_token;
                    AddLog("櫻坂-临时TOKEN获取成功！");
                }
                catch (Exception ex)
                {
                    AddLog("櫻坂-临时TOKEN获取失败" + ex.Message + ex.StackTrace);
                }
            }
            if (hinaConfig)
            {
                try
                {
                    string uploadurl = "https://api.kh.glastonr.net/v2/update_token";
                    string refreshtoken = "{\"refresh_token\":\"" + hinaMemberToken.RefreshToken + "\"}";
                    byte[] postData = Encoding.UTF8.GetBytes(refreshtoken);
                    var webclient = new WebClient();
                    webclient.Headers.Clear();
                    webclient.Headers.Add("Accept", "application/json");
                    webclient.Headers.Add("Content-Type", "application/json");
                    webclient.Headers.Add("X-Talk-App-ID", "jp.co.sonymusic.communication.keyakizaka 2.4");
                    webclient.Headers.Add("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)");
                    webclient.Headers.Add("Accept-Language", "ja-JP");
                    webclient.Headers.Add("Accept-Encoding", "gzip");
                    //webclient.Headers.Add("Connection", "Keep-Alive");
                    webclient.Headers.Add("TE", "gzip, deflate; q=0.5");
                    byte[] responseData = webclient.UploadData(uploadurl, "POST", postData);
                    string access_token = Encoding.UTF8.GetString(responseData);
                    Rrefreshtoken json = JsonConvert.DeserializeObject<Rrefreshtoken>(access_token);
                    hinaMemberToken.AccessToken = json.access_token;
                    AddLog("日向坂-临时TOKEN获取成功！");
                }
                catch (Exception ex)
                {
                    AddLog("日向坂-临时TOKEN获取失败" + ex.Message + ex.StackTrace);
                }
            }
        }

        public async static void GetMessage(MemberToken memberToken, string group)
        {
            foreach (var kvp in memberToken.memberLists)
            {
                string path = memberToken.rootPath + kvp.name + "\\";
                if (!Directory.Exists(path))
                {
                    Directory.CreateDirectory(path);
                    string textName = path + "0_0_" + DateTime.Now.ToString("yyyyMMdd") + "000000.txt";
                    File.AppendAllText(textName, "DON'T DELETE ME！");
                }
                FileTimeInfo fi = GetLatestFileTimeInfo(path);
                string exname = fi.FileName;
                string updateTime = exname.Split("_")[2].Substring(0, 14);
                DateTime originalDate = DateTime.ParseExact(updateTime, "yyyyMMddHHmmss", null);
                string created = "created_from=" + Uri.EscapeDataString(originalDate.ToString("yyyy-MM-ddTHH:mm:ssZ"));
                using var handler = new HttpClientHandler { UseCookies = false };
                using var client = new HttpClient(handler);
                byte[] responseData;
                HttpResponseMessage response ;
                switch (group)
                {
                    case "nogi":
                        {
                            if (!nogiConfig)
                                return;
                            
                            string url = "https://api.n46.glastonr.net/v2/groups/" + kvp.id + "/timeline?count=100&created_from=2023-02-02T11%3A16%3A09Z&order=asc&" + created;
                            client.DefaultRequestHeaders.Clear();
                            client.DefaultRequestHeaders.Add("Accept", "application/json");
                            //client.DefaultRequestHeaders.Add("Content-Type", "application/json");
                            client.DefaultRequestHeaders.Add("X-Talk-App-ID", "jp.co.sonymusic.communication.nogizaka 2.4");
                            client.DefaultRequestHeaders.Add("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)");
                            client.DefaultRequestHeaders.Add("Accept-Language", "ja-JP");
                            client.DefaultRequestHeaders.Add("Accept-Encoding", "gzip");
                            client.DefaultRequestHeaders.Add("TE", "gzip, deflate; q=0.5");
                            client.DefaultRequestHeaders.Add("Authorization", $"Bearer {memberToken.AccessToken}");
                            client.DefaultRequestHeaders.Connection.Add("Keep-Alive");

                            response = await client.GetAsync(url);
                            responseData = await response.Content.ReadAsByteArrayAsync();

                            break;
                        }
                    case "saku":
                        {
                            if (!sakuConfig)
                                return;
                            string url = "https://api.s46.glastonr.net/v2/groups/" + kvp.id + "/timeline?count=100&created_from=2023-02-02T11%3A16%3A09Z&order=asc&" + created;
                            client.DefaultRequestHeaders.Clear();
                            client.DefaultRequestHeaders.Add("Accept", "application/json");
                            //client.DefaultRequestHeaders.Add("Content-Type", "application/json");
                            client.DefaultRequestHeaders.Add("X-Talk-App-ID", "jp.co.sonymusic.communication.nogizaka 2.4");
                            client.DefaultRequestHeaders.Add("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)");
                            client.DefaultRequestHeaders.Add("Accept-Language", "ja-JP");
                            client.DefaultRequestHeaders.Add("Accept-Encoding", "gzip");
                            client.DefaultRequestHeaders.Add("TE", "gzip, deflate; q=0.5");
                            client.DefaultRequestHeaders.Add("Authorization", $"Bearer {memberToken.AccessToken}");
                            client.DefaultRequestHeaders.Connection.Add("Keep-Alive");

                            response = await client.GetAsync(url);
                            responseData = await response.Content.ReadAsByteArrayAsync();
                            break;
                        }
                    case "hina":
                        {
                            if(!hinaConfig)
                                return;
                            string url = "https://api.kh.glastonr.net/v2/groups/" + kvp.id + "/timeline?count=100&created_from=2023-02-02T11%3A16%3A09Z&order=asc&" + created;
                            client.DefaultRequestHeaders.Clear();
                            client.DefaultRequestHeaders.Add("Accept", "application/json");
                            //client.DefaultRequestHeaders.Add("Content-Type", "application/json");
                            client.DefaultRequestHeaders.Add("X-Talk-App-ID", "jp.co.sonymusic.communication.nogizaka 2.4");
                            client.DefaultRequestHeaders.Add("User-Agent", "Dalvik/2.1.0 (Linux; U; Android 6.0; Samsung Galaxy S7 for keyaki messages Build/MRA58K)");
                            client.DefaultRequestHeaders.Add("Accept-Language", "ja-JP");
                            client.DefaultRequestHeaders.Add("Accept-Encoding", "gzip");
                            client.DefaultRequestHeaders.Add("TE", "gzip, deflate; q=0.5");
                            client.DefaultRequestHeaders.Add("Authorization", $"Bearer {memberToken.AccessToken}");
                            client.DefaultRequestHeaders.Connection.Add("Keep-Alive");
                            response = await client.GetAsync(url);
                            responseData = await response.Content.ReadAsByteArrayAsync();
                            break;
                        }
                    default: return;
                }
                if (response.Content.Headers.ContentEncoding.Contains("gzip"))
                {
                    responseData = Decompress(responseData);
                }
                RootObject json = JsonConvert.DeserializeObject<RootObject>(Encoding.UTF8.GetString(responseData));
                AddLog("开始下载" + kvp.name + "的msg");
                DownMessage(path, json);
            }
        }


        public static void DownMessage(string path, RootObject msgJson)
        {
            int number = 1;
            if (msgJson.messages==null || msgJson.messages.Count == 0)
            {
                AddLog("没有检测到新消息");
                return;
            }
            foreach (Manager ep in msgJson.messages)
            {
                if (ep.state == "published")
                {
                    //改写日期
                    ep.published_at = ep.published_at.Replace("T", "").Replace("-", "").Replace(":", "").Replace("Z", "");
                    //创建webclient
                    WebClient client = new WebClient();

                    //判断文件类型
                    if (ep.type == "picture")
                    {
                        string name = ep.id + "_1_" + ep.published_at;
                        //创建文本
                        FileStream fs1 = new FileStream(path + name + ".txt", FileMode.Create, FileAccess.Write);
                        StreamWriter sw = new StreamWriter(fs1);
                        sw.WriteLine(ep.text);//要写入的信息。 
                        sw.Close();
                        fs1.Close();
                        //下载图片                    
                        client.DownloadFile(ep.file, path + name + ".jpg");
                    }
                    else if (ep.type == "text")
                    {
                        string name = ep.id + "_0_" + ep.published_at + ".txt";
                        FileStream fs1 = new FileStream(path + name, FileMode.Create, FileAccess.Write);
                        StreamWriter sw = new StreamWriter(fs1);
                        sw.WriteLine(ep.text);//要写入的信息。 
                        sw.Close();
                        fs1.Close();
                    }
                    else if (ep.type == "voice")
                    {
                        string name = ep.id + "_3_" + ep.published_at + ".m4a";
                        client.DownloadFile(ep.file, path + name);
                    }
                    else if (ep.type == "video")
                    {
                        string name = ep.id + "_2_" + ep.published_at + ".mp4";
                        client.DownloadFile(ep.file, path + name);
                    }
                    AddLog($"第[{number}]项 ID：[{ep.id}]已下载成功");
                }
                else
                {
                    AddLog($"第[{number}]项 ID：[{ep.id}]被删除了");
                }

                number++;
            }
        }

        /// <summary>
        /// 添加log日志
        /// </summary>
        /// <param name="message">log日志的信息</param>
        /// <param name="isError">是否为错误日志</param>
        public static void AddLog(string message, bool isError = false)
        {
            if (!isError)
            {
                Console.WriteLine($"[INFO] {DateTime.Now} {message}");
                File.AppendAllText($"log\\{DateTime.Now.ToString("yyyyMMdd")}_DownMessageFor46log.log", $"[INFO] {DateTime.Now} {message}" + Environment.NewLine);
            }
            else
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"[ERROR] {DateTime.Now} {message}");
                File.AppendAllText("log\\DownMessageFor46Error.log", $"[ERROR] {DateTime.Now} {message}" + Environment.NewLine);
                Console.ForegroundColor = ConsoleColor.White;
            }
        }

        #region 一些常用的方法

        public class FileTimeInfo
        {
            public string FileName;  //文件名
            public DateTime FileCreateTime; //创建时间            
        }
        //获取最近创建的文件名和创建时间
        //如果没有指定类型的文件，返回null
        static FileTimeInfo GetLatestFileTimeInfo(string dir)
        {
            List<FileTimeInfo> list = new List<FileTimeInfo>();
            DirectoryInfo d = new DirectoryInfo(dir);
            foreach (FileInfo fi in d.GetFiles())
            {
                if (fi.Extension == ".txt" || fi.Extension == ".mp4" || fi.Extension == ".jpg" || fi.Extension == ".m4a")
                {
                    list.Add(new FileTimeInfo()
                    {
                        FileName = fi.Name,
                        FileCreateTime = fi.CreationTime
                    });
                }
            }
            var qry = from x in list
                      orderby x.FileCreateTime
                      select x;
            return qry.LastOrDefault();
        }

        /// <summary>
        /// 解压从网络返回的gzip格式的文件
        /// </summary>
        /// <param name="bytes"></param>
        /// <returns></returns>
        public static byte[] Decompress(byte[] bytes)
        {
            using (var compressStream = new MemoryStream(bytes))
            {
                using (var zipStream = new GZipStream(compressStream, CompressionMode.Decompress))
                {
                    using (var resultStream = new MemoryStream())
                    {
                        zipStream.CopyTo(resultStream);
                        return resultStream.ToArray();
                    }
                }
            }
        }
        #endregion
    }
}
